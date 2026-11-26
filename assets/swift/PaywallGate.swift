import Observation
import SuperwallKit
import SwiftUI

// MARK: - One gate, two presenters
//
// Superwall owns presentation *when there is something to present*. Authoring a
// Superwall paywall requires a browser editor session with a pairing code, which
// cannot be automated — so a run that only wired campaigns would ship an app
// where every gate silently falls open and free equals Pro.
//
// This gate closes that hole. It asks Superwall first; if the placement skips
// (no campaign, no paywall assigned, holdout, offline, error) it presents the
// native paywall built from the RevenueCat offering instead. The app therefore
// always has a working, App-Review-compliant purchase flow, and designing a
// Superwall paywall later is an upgrade rather than a prerequisite.
//
// Attach it once, near the root:
//
//     .paywallGate()
//
// and fire gates through it:
//
//     PaywallGate.shared.present(Placement.feature(Placement.Feature.insights)) {
//         // runs only when the user is entitled, or when nothing gated it
//     }

@MainActor
@Observable
final class PaywallGate {
    static let shared = PaywallGate()

    /// Set when Superwall declined to present and the native paywall should take
    /// over. The root view observes this and shows a sheet.
    private(set) var pendingNativePresentation: Presentation?

    struct Presentation: Identifiable {
        let id = UUID()
        let placement: String
        let onEntitled: (() -> Void)?
    }

    private init() {}

    /// - Parameter onEntitled: runs when the user already has the entitlement,
    ///   completes a purchase, or when nothing gated the action at all.
    func present(_ placement: String, onEntitled: (() -> Void)? = nil) {
        let handler = PaywallPresentationHandler()

        // A skip means no campaign matched, no paywall is assigned, the user is
        // a holdout, or the device is offline. Superwall still runs the feature
        // block in that case, so the skip has to be recorded *first* and the
        // block has to check it — otherwise a missing campaign silently unlocks
        // the feature for free.
        var superwallDeclined = false
        handler.onSkip { _ in superwallDeclined = true }
        handler.onError { _ in superwallDeclined = true }

        Superwall.shared.register(placement: placement, handler: handler) { [weak self] in
            Task { @MainActor in
                guard let self else { return }
                if superwallDeclined && !RCPurchaseController.shared.isProActive {
                    self.pendingNativePresentation = Presentation(placement: placement,
                                                                  onEntitled: onEntitled)
                } else {
                    onEntitled?()
                }
            }
        }
    }

    func dismissNative(entitled: Bool) {
        let presentation = pendingNativePresentation
        pendingNativePresentation = nil
        if entitled { presentation?.onEntitled?() }
    }
}

private struct PaywallGateModifier: ViewModifier {
    @State private var gate = PaywallGate.shared

    func body(content: Content) -> some View {
        content
            .sheet(item: Binding(
                get: { gate.pendingNativePresentation },
                set: { if $0 == nil { gate.dismissNative(entitled: false) } }
            )) { presentation in
                NativePaywallView(placement: presentation.placement) { entitled in
                    gate.dismissNative(entitled: entitled)
                }
            }
    }
}

extension View {
    /// Attach once at the root. Without it, a Superwall-less build has no paywall.
    func paywallGate() -> some View {
        modifier(PaywallGateModifier())
    }
}
