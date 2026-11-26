import Foundation

/// Public runtime configuration only. Provider credentials belong on the server
/// and are never compiled into an App Store binary.
///
/// Every value here arrives through `Info.plist`, which in turn reads a build
/// setting defined in both configurations of `project.pbxproj`. That indirection
/// is what lets Debug and Release point at different backends without a single
/// hardcoded string in Swift.
///
/// RevenueCat's `appl_…` and Superwall's `pk_…` keys deliberately do *not* go
/// through here — they are client SDK keys, they never vary per environment, and
/// routing them through this file only obscures them.
enum AppConfiguration {

    // MARK: - Backend

    /// The Supabase project behind the app.
    ///
    /// The publishable key is not a secret — it identifies the project and
    /// nothing else. Every row it can reach is fenced off by row-level security
    /// tied to the caller's identity, and third-party credentials stay in the
    /// edge function's secrets where the binary can never see them.
    struct SupabaseConfiguration: Sendable {
        let url: URL
        let publishableKey: String
    }

    static var supabase: SupabaseConfiguration? {
        guard let url = configuredHTTPSURL(
            infoKey: "__APP_NAME__SupabaseURL",
            debugEnvironmentKey: "__UPPER_NAME___SUPABASE_URL"
        ) else { return nil }

        guard let key = configuredValue(
            infoKey: "__APP_NAME__SupabasePublishableKey",
            debugEnvironmentKey: "__UPPER_NAME___SUPABASE_PUBLISHABLE_KEY"
        ) else { return nil }

        return SupabaseConfiguration(url: url, publishableKey: key)
    }

    // MARK: - Marketing site

    /// Terms and privacy pages the paywall links to. App Review requires both to
    /// resolve, so this falls back to the production host rather than returning
    /// nil and rendering a dead link.
    private static let productionWebsiteURL = URL(string: "https://__WEBSITE_HOST__")

    static var websiteBaseURL: URL? {
        configuredHTTPSURL(
            infoKey: "__APP_NAME__WebsiteBaseURL",
            debugEnvironmentKey: "__UPPER_NAME___WEBSITE_URL"
        ) ?? productionWebsiteURL
    }

    static func websitePage(_ path: String) -> URL? {
        websiteBaseURL?.appending(path: path)
    }

    // MARK: - Reading and validating

    private static func configuredHTTPSURL(infoKey: String, debugEnvironmentKey: String) -> URL? {
        #if DEBUG
        if let value = ProcessInfo.processInfo.environment[debugEnvironmentKey],
           let url = validatedHTTPSURL(value) {
            return url
        }
        #endif

        guard let value = Bundle.main.object(forInfoDictionaryKey: infoKey) as? String else { return nil }
        return validatedHTTPSURL(value)
    }

    /// A plain string setting, held to the same placeholder checks as the URLs so
    /// a half-configured build fails closed instead of talking to nothing.
    private static func configuredValue(infoKey: String, debugEnvironmentKey: String) -> String? {
        #if DEBUG
        if let value = ProcessInfo.processInfo.environment[debugEnvironmentKey],
           let cleaned = validatedValue(value) {
            return cleaned
        }
        #endif

        guard let value = Bundle.main.object(forInfoDictionaryKey: infoKey) as? String else { return nil }
        return validatedValue(value)
    }

    private static func validatedValue(_ rawValue: String) -> String? {
        let value = rawValue.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !value.isEmpty, !value.localizedCaseInsensitiveContains("YOUR_") else { return nil }
        return value
    }

    /// An unset build setting expands to an empty string, and a half-filled
    /// template still contains its placeholder — both must read as "not
    /// configured" rather than producing a URL that silently fails at runtime.
    private static func validatedHTTPSURL(_ rawValue: String) -> URL? {
        let value = rawValue.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !value.isEmpty,
              !value.localizedCaseInsensitiveContains("YOUR_"),
              !value.localizedCaseInsensitiveContains("example.com"),
              let url = URL(string: value),
              url.scheme == "https",
              url.host != nil else { return nil }
        return url
    }
}
