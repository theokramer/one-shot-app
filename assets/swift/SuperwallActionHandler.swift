import AVFoundation
import SuperwallKit
import UserNotifications

// MARK: - Bridging Superwall flows and paywalls to native iOS behaviour
//
// Permission screens in the onboarding Flow are built in the Superwall dashboard,
// not in Swift — but only the app can raise a native permission prompt. Without a
// delegate on this side, taps on those buttons silently do nothing, which looks
// exactly like a Superwall outage and isn't.
//
// Two paths must both be handled, because which one fires depends on how the
// button was wired in the editor:
//
//   • The editor's built-in "Request permission" action prompts natively itself
//     and only reports back through `handleSuperwallEvent`.
//   • A button set up as a plain "Custom action" arrives at
//     `handleCustomPaywallAction(withName:)` instead, and the app must do the
//     work. Matching is on lowercased substring because the exact action name is
//     whatever the editor author typed.
//
// Add a branch here for every permission that appears in the flow, and make sure
// each one has a matching usage string in Info.plist. All three or none.
@MainActor
final class SuperwallActionHandler: SuperwallDelegate {
    static let shared = SuperwallActionHandler()

    private init() {}

    func handleCustomPaywallAction(withName name: String) {
        let key = name.lowercased()

        if key.contains("camera") {
            Task { _ = await AVCaptureDevice.requestAccess(for: .video) }
        } else if key.contains("notification") {
            Task {
                _ = try? await UNUserNotificationCenter.current()
                    .requestAuthorization(options: [.alert, .badge, .sound])
            }
        }
        // Uncomment alongside a LocationProvider in Services/ and an
        // NSLocationWhenInUseUsageDescription entry in Info.plist:
        //
        // else if key.contains("location") {
        //     LocationProvider.shared.requestAccess()
        // }
    }

    func handleSuperwallEvent(withInfo eventInfo: SuperwallEventInfo) {
        switch eventInfo.event {
        case .permissionGranted, .permissionDenied, .permissionRequested:
            // The SDK already requested the permission natively for this event;
            // nothing to trigger here, but logging it makes future paywall-button
            // issues visible in the device console.
            print("[Superwall] \(eventInfo.event)")
        default:
            break
        }
    }
}
