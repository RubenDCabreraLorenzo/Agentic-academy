/** ARIA tabs: arrow keys move and select, Home and End jump, and only the active tab is a tab stop. */
import { useId, type KeyboardEvent, type ReactNode } from "react";

export interface TabItem {
  id: string;
  label: string;
}

export function Tabs({
  label,
  tabs,
  active,
  onSelect,
  children,
}: {
  label: string;
  tabs: TabItem[];
  active: string;
  onSelect: (id: string) => void;
  children: ReactNode;
}) {
  const base = useId();
  const tabId = (id: string) => `${base}-tab-${id}`;
  const panelId = `${base}-panel`;

  const onKey = (event: KeyboardEvent<HTMLButtonElement>, index: number) => {
    const count = tabs.length;
    const targets: Record<string, number> = { ArrowRight: (index + 1) % count, ArrowLeft: (index + count - 1) % count, Home: 0, End: count - 1 };
    const target = targets[event.key];
    if (target === undefined) return;
    event.preventDefault();
    const next = tabs[target];
    if (!next) return;
    onSelect(next.id);
    document.getElementById(tabId(next.id))?.focus();
  };

  return (
    <div className="tabs">
      <div role="tablist" aria-label={label} className="tabs-list">
        {tabs.map((tab, i) => (
          <button
            key={tab.id}
            id={tabId(tab.id)}
            role="tab"
            type="button"
            className="tab"
            aria-selected={tab.id === active}
            aria-controls={panelId}
            tabIndex={tab.id === active ? 0 : -1}
            onClick={() => onSelect(tab.id)}
            onKeyDown={(e) => onKey(e, i)}
          >
            {tab.label}
          </button>
        ))}
      </div>
      <div id={panelId} role="tabpanel" aria-labelledby={tabId(active)} className="tabs-panel">
        {children}
      </div>
    </div>
  );
}
