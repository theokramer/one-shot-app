/**
 * TEMPLATE (from a shipped app). Meta + TikTok attribution, started after the ATT answer.
 * Copy to src/core/ads.ts. Needs: expo-tracking-transparency, react-native-fbsdk-next (plugin in app.json
 * with appID, clientToken, displayName, isAutoInitEnabled:false, autoLogAppEventsEnabled:false,
 * advertiserIDCollectionEnabled:true), and react-native-purchases.
 * TikTok Events API uses server-side credentials. This template does not fetch them.
 */
import { getTrackingPermissionsAsync, requestTrackingPermissionsAsync } from 'expo-tracking-transparency';
import Purchases from 'react-native-purchases';
import { AppEventsLogger, Settings } from 'react-native-fbsdk-next';

let started = false;

/**
 * Initialize attribution and collect device identifiers after ATT consent.
 */
export async function startAds(ask: boolean) {
  if (started) return;
  try {
    let { status, canAskAgain } = await getTrackingPermissionsAsync();
    if (status === 'undetermined' && ask && canAskAgain) status = (await requestTrackingPermissionsAsync()).status;
    if (status !== 'granted' || started) return;
    started = true;
    await Settings.setAdvertiserTrackingEnabled(true);
    Settings.initializeSDK();
    // Lets RevenueCat match purchases to the same ad networks.
    await Purchases.collectDeviceIdentifiers();
    const anon = await AppEventsLogger.getAnonymousID();
    if (anon) await Purchases.setFBAnonymousID(anon);
  } catch { /* attribution must never break the app */ }
}
