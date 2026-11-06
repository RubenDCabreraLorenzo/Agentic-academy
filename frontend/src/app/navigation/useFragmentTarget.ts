/**
 * Fragment protocol (routes contract, research R9). The browser handles a fragment before the content
 * exists, so the page brings the target into view once it has rendered, and keeps it there while code
 * and diagrams change height. It stops at the first sign that the person is moving through the page.
 */
import { useEffect } from "react";
import { useLocation, useNavigationType } from "react-router";

const SETTLE_MS = 3000;
const INPUT_EVENTS = ["wheel", "touchmove", "keydown", "pointerdown"];
const LISTENER = { capture: true, passive: true } as const;
// A load keeps this key; returning to an entry later is back navigation, which the browser restores.
const LOADED_KEY = (window.history.state as { key?: string } | null)?.key ?? "default";

function findTarget(hash: string): HTMLElement | null {
  try {
    return document.getElementById(decodeURIComponent(hash.slice(1)));
  } catch {
    return null;
  }
}

export function useFragmentTarget(ready: boolean): void {
  const { hash, key } = useLocation();
  const type = useNavigationType();

  useEffect(() => {
    if (!ready || !hash || (type === "POP" && key !== LOADED_KEY)) return;
    const target = findTarget(hash);
    if (!target) return;

    // Never smooth: it would fight the re-positioning, and reduced motion rules it out anyway.
    const place = () => target.scrollIntoView({ block: "start", behavior: "instant" });
    place();
    target.tabIndex = -1;
    target.focus({ preventScroll: true });

    const observer = typeof ResizeObserver === "undefined" ? null : new ResizeObserver(place);
    observer?.observe(document.body);
    const timer = window.setTimeout(() => stop(), SETTLE_MS);
    const stop = () => {
      observer?.disconnect();
      window.clearTimeout(timer);
      INPUT_EVENTS.forEach((e) => window.removeEventListener(e, stop, LISTENER));
    };
    INPUT_EVENTS.forEach((e) => window.addEventListener(e, stop, LISTENER));
    return stop;
  }, [ready, hash, key, type]);
}
