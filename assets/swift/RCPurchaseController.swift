import SuperwallKit
import RevenueCat
import StoreKit
import Observation

enum PurchasingError: LocalizedError {
    case sk2ProductNotFound

    var errorDescription: String? {
        switch self {
        case .sk2ProductNotFound:
            return "Superwall didn't pass a StoreKit 2 product to purchase. Are you sure you're not "
                + "configuring Superwall with a SuperwallOption to use StoreKit 1?"
        }
    }
}

/// RevenueCat is the source of truth for purchases and entitlements; Superwall
/// stays a thin paywall-presentation layer synced through `syncSubscriptionStatus()`.
@MainActor
@Observable
final class RCPurchaseController: PurchaseController {

    static let proEntitlementID = "pro"

    /// The app entry point assigns this right after `init()`. `PaywallGate` needs
    /// entitlement state from a non-SwiftUI context, where `@Environment` is not
    /// available, and a second instance would report a stale `isProActive`.
    static private(set) var shared: RCPurchaseController!

    private(set) var isProActive = false

    init() {
        Self.shared = self
    }

    // MARK: Sync Subscription Status
    /// Makes sure that Superwall knows the customer's entitlements by
    /// changing `Superwall.shared.subscriptionStatus`.
    func syncSubscriptionStatus() {
        assert(Purchases.isConfigured, "You must configure RevenueCat before calling this method.")
        Task {
            for await customerInfo in Purchases.shared.customerInfoStream {
                // Gets called whenever new CustomerInfo is available
                let superwallEntitlements = customerInfo.entitlements.activeInCurrentEnvironment.keys.map {
                    Entitlement(id: $0)
                }
                isProActive = customerInfo.entitlements[Self.proEntitlementID]?.isActive == true
                Superwall.shared.subscriptionStatus = .active(Set(superwallEntitlements))
            }
        }
    }

    // MARK: Handle Purchases
    /// Makes a purchase with RevenueCat and returns its result. This gets called when
    /// someone tries to purchase a product on one of your paywalls.
    func purchase(product: SuperwallKit.StoreProduct) async -> PurchaseResult {
        do {
            guard let sk2Product = product.sk2Product else {
                throw PurchasingError.sk2ProductNotFound
            }
            let storeProduct = RevenueCat.StoreProduct(sk2Product: sk2Product)
            let revenueCatResult = try await Purchases.shared.purchase(product: storeProduct)
            if revenueCatResult.userCancelled {
                return .cancelled
            } else {
                return .purchased
            }
        } catch let error as ErrorCode {
            if error == .paymentPendingError {
                return .pending
            } else {
                return .failed(error)
            }
        } catch {
            return .failed(error)
        }
    }

    // MARK: Handle Restores
    /// Makes a restore with RevenueCat and returns `.restored`, unless an error is thrown.
    /// This gets called when someone tries to restore purchases on one of your paywalls.
    func restorePurchases() async -> RestorationResult {
        do {
            _ = try await Purchases.shared.restorePurchases()
            return .restored
        } catch {
            return .failed(error)
        }
    }
}
