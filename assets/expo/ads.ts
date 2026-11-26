/**
 * TEMPLATE (from a shipped app). Meta + TikTok attribution, started after the ATT answer.
 * Copy to src/core/ads.ts. Needs: expo-tracking-transparency, react-native-fbsdk-next (plugin in app.json
 * with appID, clientToken, displayName, isAutoInitEnabled:false, autoLogAppEventsEnabled:false,
 * advertiserIDCollectionEnabled:true), react-native-tiktok-business-sdk, react-native-purchases.
 * config.ts exports API_URL, BUNDLE_ID and TIKTOK = { appId: '', accessToken: '' } (empty until launch;
 * the Worker's /v1/config supplies the real values after `wrangler secret put`). Drop the TikTok lines if
 * that module isn't ticked. For Apple Search Ads also call Purchases.enableAdServicesAttributionTokenCollection().
 */
import { getTrackingPermissionsAsync, requestTrackingPermissionsAsync } from 'expo-tracking-transparency';
import Purchases from 'react-native-purchases';
import { AppEventsLogger, Settings } from 'react-native-fbsdk-next';
import { TikTokBusiness } from 'react-native-tiktok-business-sdk';
import { API_URL, BUNDLE_ID, TIKTOK } from './config';

let started = false;

/**
 * Ad attribution for Meta and TikTok. Both SDKs log the install and App Store purchases themselves,
 * so ad dashboards can show which campaigns bring paying users.
 * Starts only once the person has answered Apple's tracking prompt; without consent
 * the SDKs still report aggregated, non-identifying data (SKAdNetwork / AEM).
 */
export async function startAds(ask: boolean) {
  if (started) return;
  try {
    let { status, canAskAgain } = await getTrackingPermissionsAsync();
    if (status === 'undetermined' && ask && canAskAgain) status = (await requestTrackingPermissionsAsync()).status;
    if (status === 'undetermined' || started) return;
    started = true;
    const granted = status === 'granted';
    await Settings.setAdvertiserTrackingEnabled(granted);
    Settings.initializeSDK();
    // The TikTok app can only be registered once the app is live, so its IDs come from the server.
    const tt = await tiktokIds();
    if (tt.appId && tt.accessToken) await TikTokBusiness.initializeSdk(BUNDLE_ID, tt.appId, tt.accessToken, false);
    // Lets RevenueCat match purchases to the same ad networks.
    await Purchases.collectDeviceIdentifiers();
    const anon = await AppEventsLogger.getAnonymousID();
    if (anon) await Purchases.setFBAnonymousID(anon);
  } catch { /* attribution must never break the app */ }
}

async function tiktokIds(): Promise<{ appId: string; accessToken: string }> {
  try {
    const ctl = new AbortController(), t = setTimeout(() => ctl.abort(), 5000);
    const r = await fetch(`${API_URL}/v1/config`, { signal: ctl.signal }).finally(() => clearTimeout(t));
    const c = (await r.json()) as { tiktok?: { appId?: string; accessToken?: string } };
    if (c.tiktok?.appId && c.tiktok.accessToken) return { appId: c.tiktok.appId, accessToken: c.tiktok.accessToken };
  } catch { /* offline: fall back to the built-in values */ }
  return TIKTOK;
}
