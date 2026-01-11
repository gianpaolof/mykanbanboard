// components/settings/KeyboardShortcutsSettings.tsx - Keyboard shortcuts reference
import { cn } from '@/lib/utils';
import { SettingsSection } from './SettingsSection';

interface Shortcut {
  category: string;
  items: {
    action: string;
    keys: string[];
  }[];
}

const SHORTCUTS: Shortcut[] = [
  {
    category: 'General',
    items: [
      { action: 'Open command palette', keys: ['⌘', 'K'] },
      { action: 'Open settings', keys: ['⌘', ','] },
      { action: 'Toggle sidebar', keys: ['⌘', '/'] },
      { action: 'Close modal/panel', keys: ['Esc'] },
    ],
  },
  {
    category: 'Actions',
    items: [
      { action: 'Create new ticket', keys: ['⌘', 'N'] },
      { action: 'Open AI assistant', keys: ['⌘', '⇧', 'A'] },
      { action: 'Get daily summary', keys: ['⌘', '⇧', 'S'] },
    ],
  },
  {
    category: 'Navigation',
    items: [
      { action: 'Switch to Board view', keys: ['⌘', '1'] },
      { action: 'Switch to List view', keys: ['⌘', '2'] },
      { action: 'Switch to Timeline view', keys: ['⌘', '3'] },
    ],
  },
];

function Kbd({ children }: { children: string }) {
  return (
    <kbd
      className={cn(
        'inline-flex items-center justify-center',
        'min-w-[24px] h-6 px-2',
        'rounded border border-border-subtle bg-bg-tertiary',
        'font-mono text-xs font-medium text-text-secondary',
        'shadow-sm'
      )}
    >
      {children}
    </kbd>
  );
}

export function KeyboardShortcutsSettings() {
  return (
    <div className="space-y-8">
      <SettingsSection
        title="Keyboard Shortcuts"
        description="Learn keyboard shortcuts to speed up your workflow"
      >
        <div className="space-y-6">
          {SHORTCUTS.map((section) => (
            <div key={section.category}>
              <h4 className="text-sm font-semibold text-text-muted uppercase tracking-wide mb-3">
                {section.category}
              </h4>
              <div className="space-y-2">
                {section.items.map((item, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-3 rounded-lg bg-bg-elevated border border-border-subtle"
                  >
                    <span className="text-sm text-text-secondary">
                      {item.action}
                    </span>
                    <div className="flex items-center gap-1">
                      {item.keys.map((key, keyIndex) => (
                        <Kbd key={keyIndex}>{key}</Kbd>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </SettingsSection>

      {/* Customization Note */}
      <div
        className={cn(
          'p-4 rounded-lg border',
          'bg-bg-elevated border-border-subtle'
        )}
      >
        <p className="text-sm text-text-tertiary">
          Custom keyboard shortcuts will be available in a future update.
          For now, these are the default shortcuts for Kanban AI.
        </p>
      </div>
    </div>
  );
}
