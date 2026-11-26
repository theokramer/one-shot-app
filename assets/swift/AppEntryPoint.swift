import SwiftUI
import SuperwallKit
import RevenueCat

// MARK: - Launch
//
// Configuration order is load-bearing:
//   1. RevenueCat first — the purchase controller asserts `Purchases.isConfigured`.
//   2. Superwall *with* the controller — configuring without one lets Superwall
//      transact directly, which breaks the single source of truth for entitlements.
//   3. `syncSubscriptionStatus()` after both, so the CustomerInfo stream can push
//      entitlements into `Superwall.shared.subscriptionStatus`.
//   4. The delegate last, so permission buttons in the onboarding Flow work.
//
// Both keys below are public client SDK keys and belong in source. They are not
// routed through AppConfiguration — that indirection exists for backend URLs and
// per-environment values, which these are not.

@main
struct __APP_NAME__App: App {
    @State private var store = AppStore()
    @State private var purchases: RCPurchaseController

    init() {
        Purchases.configure(withAPIKey: "__REVENUECAT_PUBLIC_KEY__")

        // RevenueCat owns purchases and entitlements; Superwall stays a thin
        // paywall-presentation layer synced through the controller below.
        let purchaseController = RCPurchaseController()
        Superwall.configure(apiKey: "__SUPERWALL_PUBLIC_KEY__", purchaseController: purchaseController)
        purchaseController.syncSubscriptionStatus()
        Superwall.shared.delegate = SuperwallActionHandler.shared

        _purchases = State(initialValue: purchaseController)
    }

    var body: some Scene {
        WindowGroup {
            RootView(store: store)
                .environment(purchases)
                .preferredColorScheme(.dark)
                .tint(Theme.accent)
        }
    }
}
