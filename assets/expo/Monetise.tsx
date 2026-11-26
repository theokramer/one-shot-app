/**
 * TEMPLATE (from a shipped app). Superwall presents, RevenueCat buys. Copy to src/ui/Monetise.tsx
 * and wrap the root layout: <Monetise>{children}</Monetise>.
 *
 * Expects from src/core/pro.ts (write it per app):
 *   usePro          zustand store { isPro, restore(): Promise<boolean> }
 *   startPurchases  Purchases.configure + logIn(deviceId) + customerInfo listener → usePro
 *   setPresenter    registers the function gate() uses to show a placement
 *   openNative      pushes the native /paywall route (the fallback)
 *   setPresenting / closed   bookkeeping so two paywalls never stack
 *   Placement       union of placement names ('onboarding_paywall' | 'feature_x' | 'paywall_generic' …)
 * Expects src/core/ads.ts (assets/expo/ads.ts) and src/core/config.ts (SUPERWALL_KEY: public pk_… key).
 *
 * The rule that froze an onboarding at 200 % CPU: Superwall hook functions change identity every
 * render. Never put them in effect deps; call them through refs, as below.
 */
import { CustomPurchaseControllerProvider, SuperwallProvider, usePlacement, useSuperwall, useUser } from 'expo-superwall';
import Purchases from 'react-native-purchases';
import { useEffect, useRef, type ReactNode } from 'react';
import { startAds } from '../core/ads';
import { SUPERWALL_KEY } from '../core/config';
import { useApp } from '../core/store';
import { closed, openNative, setPresenting, setPresenter, startPurchases, usePro, type Placement } from '../core/pro';

/** Superwall decides which paywall to show; RevenueCat performs every purchase. */
const controller = {
  onPurchase: async (p: { productId: string }) => {
    try {
      const [product] = await Purchases.getProducts([p.productId]);
      if (!product) return { type: 'failed' as const, error: 'Product unavailable' };
      const { customerInfo } = await Purchases.purchaseStoreProduct(product);
      usePro.setState({ isPro: !!customerInfo.entitlements.active.pro });
      return { type: 'purchased' as const };
    } catch (e) {
      const c = e as { userCancelled?: boolean | null; message?: string };
      return c.userCancelled ? { type: 'cancelled' as const } : { type: 'failed' as const, error: c.message ?? 'Purchase failed' };
    }
  },
  onPurchaseRestore: async () => ((await usePro.getState().restore()) ? { type: 'restored' as const } : { type: 'failed' as const, error: 'Nothing to restore' }),
};

function Bridge() {
  const { setSubscriptionStatus, update } = useUser();
  const answers = useApp((s) => s.answers);
  // Lets campaigns pick a paywall by what people told the onboarding.
  const updateRef = useRef(update); updateRef.current = update;
  // Only when the answers change: `update` itself changes after every Superwall user event.
  useEffect(() => { updateRef.current({ goal: answers.goal, pains: answers.pains.join(','), styles: answers.styles.join(','), first_room: answers.room }).catch(() => {}); }, [answers]);
  const dismiss = useSuperwall((s) => s.dismiss);
  const dismissRef = useRef(dismiss); dismissRef.current = dismiss;
  const isPro = usePro((s) => s.isPro);
  const ask = useRef<{ placement: Placement; unlocked: () => void; shown: boolean; done: boolean } | null>(null);
  const fallback = () => { const a = ask.current; if (!a || a.done || a.shown) return; a.done = true; openNative(a.placement, a.unlocked); };
  const { registerPlacement } = usePlacement({
    // Arrived after the native paywall already took over: close it rather than stack two.
    onPresent: () => { const a = ask.current; if (!a) return; if (a.done) { void dismissRef.current(); return; } a.shown = true; setPresenting(true); },
    onSkip: fallback, onError: fallback,
    onDismiss: (_, r) => { const a = ask.current; if (!a || a.done) return; a.done = true; if (r.type === 'purchased' || r.type === 'restored') a.unlocked(); closed(); },
  });
  const reg = useRef(registerPlacement); reg.current = registerPlacement;
  useEffect(() => {
    startPurchases(() => {});
    // People past onboarding are asked on launch; new ones at the end of onboarding.
    void startAds(useApp.getState().onboarded);
    setPresenter((placement, unlocked) => {
      ask.current = { placement, unlocked, shown: false, done: false };
      reg.current({ placement, params: {} }).catch(fallback);
      // Offline or unconfigured: never leave a tap unanswered.
      setTimeout(fallback, 4000);
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  const statusRef = useRef(setSubscriptionStatus); statusRef.current = setSubscriptionStatus;
  useEffect(() => { statusRef.current(isPro ? { status: 'ACTIVE', entitlements: [{ id: 'pro', type: 'SERVICE_LEVEL' }] } : { status: 'INACTIVE' }).catch(() => {}); }, [isPro]);
  return null;
}

export function Monetise({ children }: { children: ReactNode }) {
  return (
    <CustomPurchaseControllerProvider controller={controller}>
      <SuperwallProvider apiKeys={{ ios: SUPERWALL_KEY }}><Bridge />{children}</SuperwallProvider>
    </CustomPurchaseControllerProvider>
  );
}
