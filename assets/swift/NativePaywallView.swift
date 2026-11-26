import RevenueCat
import SwiftUI

// MARK: - The paywall that always exists
//
// Built from the RevenueCat offering, so prices, durations and trial lengths are
// whatever the store says — never hardcoded, never stale.
//
// Everything App Review guideline 3.1.2 requires is on this screen without
// scrolling or tapping: title, duration, price per period, what the trial does
// when it ends, links to Terms and Privacy, and a visible Restore control. That
// list is the most common subscription rejection; treat it as load-bearing, not
// as decoration.
//
// `PaywallCopy` is the only thing an app customises. Fill it from docs/SPEC.md's
// free/pro table so the bullets and the gate never drift apart.

struct PaywallCopy {
    var title: LocalizedStringKey
    var subtitle: LocalizedStringKey
    /// SF Symbol + one short line each. Four to six; more reads as a spec sheet.
    var benefits: [(symbol: String, text: LocalizedStringKey)]
    var termsURL: URL?
    var privacyURL: URL?

    static var current: PaywallCopy = PaywallCopy(
        title: "paywall.title",
        subtitle: "paywall.subtitle",
        benefits: [],
        termsURL: nil,
        privacyURL: nil
    )
}

struct NativePaywallView: View {
    let placement: String
    let onFinish: (_ entitled: Bool) -> Void

    @Environment(\.openURL) private var openURL
    @State private var offering: Offering?
    @State private var selected: Package?
    @State private var isWorking = false
    @State private var errorMessage: String?
    @State private var loadFailed = false

    private var copy: PaywallCopy { PaywallCopy.current }

    var body: some View {
        VStack(spacing: 0) {
            header
            ScrollView {
                VStack(spacing: Theme.Space.lg) {
                    intro
                    benefits
                    packages
                    legal
                }
                .padding(.horizontal, Theme.Space.lg)
                .padding(.bottom, Theme.Space.xxl)
            }
            footer
        }
        .background(Theme.Palette.background)
        .task { await load() }
        .alert("paywall.errorTitle", isPresented: Binding(
            get: { errorMessage != nil },
            set: { if !$0 { errorMessage = nil } }
        )) {
            Button("action.done", role: .cancel) { errorMessage = nil }
        } message: {
            Text(errorMessage ?? "")
        }
    }

    // MARK: Sections

    private var header: some View {
        HStack {
            Button {
                onFinish(false)
            } label: {
                Image(systemName: "xmark")
                    .font(.system(size: 15, weight: .semibold))
                    .foregroundStyle(Theme.Palette.inkMuted)
                    .frame(width: 36, height: 36)
                    .background(Theme.Palette.surfaceSunken, in: Circle())
            }
            .accessibilityLabel("action.close")
            Spacer()
            Button("settings.restore") { Task { await restore() } }
                .typeStyle(.label)
                .foregroundStyle(Theme.Palette.inkMuted)
        }
        .padding(.horizontal, Theme.Space.lg)
        .padding(.top, Theme.Space.md)
    }

    private var intro: some View {
        VStack(spacing: Theme.Space.xs) {
            Text(copy.title)
                .typeStyle(.display)
                .foregroundStyle(Theme.Palette.ink)
                .multilineTextAlignment(.center)
            Text(copy.subtitle)
                .typeStyle(.body)
                .foregroundStyle(Theme.Palette.inkMuted)
                .multilineTextAlignment(.center)
        }
        .padding(.top, Theme.Space.md)
    }

    private var benefits: some View {
        SurfaceCard {
            VStack(alignment: .leading, spacing: Theme.Space.sm) {
                ForEach(Array(copy.benefits.enumerated()), id: \.offset) { _, benefit in
                    HStack(spacing: Theme.Space.sm) {
                        Image(systemName: benefit.symbol)
                            .font(.system(size: 15, weight: .semibold))
                            .foregroundStyle(Theme.Palette.accent)
                            .frame(width: 26)
                        Text(benefit.text)
                            .typeStyle(.body)
                            .foregroundStyle(Theme.Palette.ink)
                        Spacer(minLength: 0)
                    }
                }
            }
        }
    }

    @ViewBuilder
    private var packages: some View {
        if let offering {
            VStack(spacing: Theme.Space.sm) {
                ForEach(offering.availablePackages, id: \.identifier) { package in
                    PackageRow(package: package, isSelected: selected?.identifier == package.identifier) {
                        selected = package
                    }
                }
            }
        } else if loadFailed {
            SurfaceCard {
                VStack(spacing: Theme.Space.sm) {
                    Text("paywall.loadFailed")
                        .typeStyle(.body)
                        .foregroundStyle(Theme.Palette.inkMuted)
                        .multilineTextAlignment(.center)
                    PillButton(title: "paywall.retry", kind: .secondary) {
                        Task { await load() }
                    }
                }
                .frame(maxWidth: .infinity)
            }
        } else {
            ProgressView()
                .tint(Theme.Palette.accent)
                .padding(.vertical, Theme.Space.xxl)
        }
    }

    /// Both links are mandatory and both must resolve, or review bounces it.
    private var legal: some View {
        HStack(spacing: Theme.Space.md) {
            if let terms = copy.termsURL {
                Button("paywall.terms") { openURL(terms) }
            }
            if let privacy = copy.privacyURL {
                Button("paywall.privacy") { openURL(privacy) }
            }
        }
        .typeStyle(.caption)
        .foregroundStyle(Theme.Palette.inkMuted)
    }

    private var footer: some View {
        VStack(spacing: Theme.Space.xs) {
            PillButton(
                title: selected?.storeProduct.introductoryDiscount != nil ? "paywall.startTrial" : "paywall.subscribe",
                systemImage: "sparkles",
                isEnabled: selected != nil && !isWorking
            ) {
                Task { await purchase() }
            }

            // The renewal terms have to be visible on the paywall itself.
            Text("paywall.renewalNote")
                .typeStyle(.caption)
                .foregroundStyle(Theme.Palette.inkMuted)
                .multilineTextAlignment(.center)
        }
        .padding(.horizontal, Theme.Space.lg)
        .padding(.bottom, Theme.Space.lg)
        .background(Theme.Palette.background)
    }

    // MARK: Work

    private func load() async {
        loadFailed = false
        do {
            let offerings = try await Purchases.shared.offerings()
            let resolved = offerings.current ?? offerings.all.values.first
            offering = resolved
            // Preselect the annual plan: it is the one carrying the trial, and a
            // preselected option converts better than an empty radio group.
            selected = resolved?.annual ?? resolved?.availablePackages.first
            loadFailed = resolved == nil
        } catch {
            loadFailed = true
        }
    }

    private func purchase() async {
        guard let package = selected else { return }
        isWorking = true
        defer { isWorking = false }
        do {
            let result = try await Purchases.shared.purchase(package: package)
            if result.userCancelled { return }
            let entitled = result.customerInfo
                .entitlements[RCPurchaseController.proEntitlementID]?.isActive == true
            onFinish(entitled)
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    private func restore() async {
        isWorking = true
        defer { isWorking = false }
        do {
            let info = try await Purchases.shared.restorePurchases()
            let entitled = info.entitlements[RCPurchaseController.proEntitlementID]?.isActive == true
            if entitled {
                onFinish(true)
            } else {
                errorMessage = String(localized: "paywall.nothingToRestore",
                                      defaultValue: "No previous purchase found for this Apple Account.")
            }
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}

// MARK: - One purchasable option

private struct PackageRow: View {
    let package: Package
    let isSelected: Bool
    let action: () -> Void

    /// "3 days free, then €29.99/year" — assembled from the store product so it
    /// can never disagree with what the user is actually charged.
    private var priceLine: String {
        let product = package.storeProduct
        let price = product.localizedPriceString
        let period = product.subscriptionPeriod?.localizedDescription ?? ""
        return period.isEmpty ? price : "\(price) / \(period)"
    }

    private var trialLine: String? {
        guard let intro = package.storeProduct.introductoryDiscount,
              intro.price == 0 else { return nil }
        return intro.subscriptionPeriod.localizedTrialDescription
    }

    var body: some View {
        Button(action: action) {
            HStack(spacing: Theme.Space.sm) {
                Image(systemName: isSelected ? "largecircle.fill.circle" : "circle")
                    .font(.system(size: 20))
                    .foregroundStyle(isSelected ? Theme.Palette.accent : Theme.Palette.rule)

                VStack(alignment: .leading, spacing: 2) {
                    Text(package.storeProduct.localizedTitle)
                        .typeStyle(.headline)
                        .foregroundStyle(Theme.Palette.ink)
                    Text(priceLine)
                        .typeStyle(.caption)
                        .foregroundStyle(Theme.Palette.inkMuted)
                    if let trialLine {
                        Text(trialLine)
                            .typeStyle(.caption)
                            .foregroundStyle(Theme.Palette.accent)
                    }
                }
                Spacer(minLength: 0)
            }
            .padding(Theme.Space.md)
            .background(
                isSelected ? Theme.Palette.accentSurface : Theme.Palette.surface,
                in: RoundedRectangle(cornerRadius: Theme.Radius.card, style: .continuous)
            )
        }
        .buttonStyle(.pressable)
    }
}

private extension SubscriptionPeriod {
    var localizedDescription: String {
        let unitName: String
        switch unit {
        case .day: unitName = String(localized: "period.day", defaultValue: "day")
        case .week: unitName = String(localized: "period.week", defaultValue: "week")
        case .month: unitName = String(localized: "period.month", defaultValue: "month")
        case .year: unitName = String(localized: "period.year", defaultValue: "year")
        @unknown default: unitName = ""
        }
        return value == 1 ? unitName : "\(value) \(unitName)"
    }

    var localizedTrialDescription: String {
        String(format: String(localized: "paywall.trialFormat %@",
                              defaultValue: "%@ free, then the price above"),
               localizedDescription)
    }
}
