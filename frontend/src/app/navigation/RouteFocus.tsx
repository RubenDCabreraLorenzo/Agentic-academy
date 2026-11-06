/**
 * Navigation protocol (routes contract). A new navigation with no fragment starts at the top, with
 * focus on the page's heading. Back and forward stay with the browser.
 */
import { useEffect, useRef } from "react";
import { useLocation, useNavigationType } from "react-router";

const HEADING_WAIT_MS = 3000;
const CAPTURE = { capture: true } as const;

function focusHeading(): boolean {
  const heading = document.querySelector<HTMLElement>("main h1");
  if (!heading) return false;
  heading.tabIndex = -1;
  heading.focus({ preventScroll: true });
  return true;
}

export function RouteFocus() {
  const { pathname, hash, key } = useLocation();
  const type = useNavigationType();
  const previousPath = useRef(pathname);
  // Until the person acts, a location change is the first load or its redirect, not a navigation.
  const acted = useRef(false);

  useEffect(() => {
    const mark = () => {
      acted.current = true;
    };
    const events = ["pointerdown", "keydown", "click"];
    events.forEach((e) => window.addEventListener(e, mark, CAPTURE));
    return () => events.forEach((e) => window.removeEventListener(e, mark, CAPTURE));
  }, []);

  useEffect(() => {
    const pathChanged = previousPath.current !== pathname;
    previousPath.current = pathname;
    if (type === "POP") return;
    // A fragment is positioned by its page once the content exists, so only leave the old position behind.
    if (!hash || pathChanged) window.scrollTo({ top: 0, behavior: "instant" });
    if (hash || !acted.current || focusHeading()) return;

    const main = document.getElementById("main");
    if (!main) return;
    const observer = new MutationObserver(() => {
      if (focusHeading()) stop();
    });
    const timer = window.setTimeout(() => {
      stop();
      main.focus({ preventScroll: true });
    }, HEADING_WAIT_MS);
    // While the page loads the person may already have moved on; do not take focus back.
    const stop = () => {
      observer.disconnect();
      window.clearTimeout(timer);
      window.removeEventListener("pointerdown", stop, CAPTURE);
      window.removeEventListener("keydown", stop, CAPTURE);
    };
    observer.observe(main, { childList: true, subtree: true });
    window.addEventListener("pointerdown", stop, CAPTURE);
    window.addEventListener("keydown", stop, CAPTURE);
    return stop;
  }, [pathname, hash, key, type]);

  return null;
}
