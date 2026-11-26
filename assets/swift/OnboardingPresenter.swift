import SwiftUI
import SuperwallKit

/// Every Superwall placement the app fires, in one place. Campaigns in the
/// dashboard bind to these strings, so a rename here silently breaks a campaign —
/// treat them as a published contract.
enum Placement {
    /// First launch. Presents the onboarding **Flow** — a separate Superwall
    /// entity from any paywall.
    static let onboardingStart = "onboarding_start"

    /// Fired when the flow completes. Presents a paywall tuned for a warm,
    /// just-onboarded user. Separate from the flow so either can be shown alone,
    /// and so the flow's answers can route to different paywall variants.
    static let onboardingPaywall = "onboarding_paywall"

    /// A generic upgrade tap — settings row, banner, "go Pro" button.
    static let generic = "paywall_generic"

    /// A specific gated capability. The campaign behind it can show a paywall
    /// whose copy names that feature.
    static func feature(_ name: String) -> String { "feature_\(name)" }
}

// MARK: - Onboarding presentation
//
// The onboarding lives in Superwall as a Flow, so copy, question order, and the
// paywall that follows can change without shipping a build. The native
// `OnboardingView` stays in the app as the fallback: if the placement has no
// campaign, the device is offline, or Superwall errors, the user still gets an
// onboarding rather than being dropped into an empty app.

@MainActor
@Observable
final class OnboardingPresenter {

    enum Phase {
        /// Nothing asked for yet.
        case idle
        /// Superwall has been asked to present; wait rather than flashing the
        /// native flow behind it.
        case presenting
        /// Superwall could not present. Run the built-in flow instead.
        case fallback
        /// The flow finished — either in Superwall or natively.
        case done
    }

    private(set) var phase: Phase = .idle

    /// Asks Superwall for the onboarding Flow exactly once per launch.
    func start(store: AppStore) {
        guard phase == .idle else { return }
        phase = .presenting

        let handler = PaywallPresentationHandler()

        // A skip means no campaign matched, the user is a holdout, or the
        // placement isn't wired up yet. In every one of those cases the register
        // feature block still fires, so record the skip first and let the block
        // read it.
        handler.onSkip { [weak self] _ in
            Task { @MainActor in self?.phase = .fallback }
        }
        handler.onError { [weak self] _ in
            Task { @MainActor in self?.phase = .fallback }
        }

        Superwall.shared.register(placement: Placement.onboardingStart, handler: handler) { [weak self] in
            Task { @MainActor in
                guard let self else { return }
                // Only treat this as a real completion when Superwall actually
                // showed the flow. A skipped placement hands control back to the
                // native onboarding instead of silently marking it finished —
                // without this guard a user who never saw onboarding would never
                // be offered it again.
                guard self.phase != .fallback else { return }
                self.finish(store: store)
            }
        }
    }

    /// Called when the built-in flow finishes, so both paths end in one place.
    func finishedNatively(store: AppStore) {
        finish(store: store)
    }

    private func finish(store: AppStore) {
        phase = .done
        store.hasOnboarded = true

        // Chain to the paywall as a *separate* placement rather than baking it
        // into the flow. Answers collected during the flow were written as
        // Superwall user attributes, so audience rules on `onboardingPaywall` can
        // route different answers to different paywall variants — and removing
        // the campaign turns the chain off without a code change.
        Superwall.shared.register(placement: Placement.onboardingPaywall)
    }
}
