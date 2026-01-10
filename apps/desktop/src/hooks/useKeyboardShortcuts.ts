import { useEffect } from 'react';

/**
 * Keyboard shortcut configuration
 */
export interface KeyboardShortcut {
  key: string;
  metaKey?: boolean;
  ctrlKey?: boolean;
  shiftKey?: boolean;
  altKey?: boolean;
  callback: () => void;
}

/**
 * Custom hook for managing global keyboard shortcuts
 *
 * @example
 * ```tsx
 * useKeyboardShortcuts([
 *   { key: 'k', metaKey: true, callback: () => setCommandPaletteOpen(true) },
 *   { key: 'n', metaKey: true, callback: () => createNewTicket() },
 * ]);
 * ```
 */
export function useKeyboardShortcuts(shortcuts: KeyboardShortcut[]) {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      for (const shortcut of shortcuts) {
        const metaMatch = shortcut.metaKey === undefined || shortcut.metaKey === e.metaKey;
        const ctrlMatch = shortcut.ctrlKey === undefined || shortcut.ctrlKey === e.ctrlKey;
        const shiftMatch = shortcut.shiftKey === undefined || shortcut.shiftKey === e.shiftKey;
        const altMatch = shortcut.altKey === undefined || shortcut.altKey === e.altKey;
        const keyMatch = e.key.toLowerCase() === shortcut.key.toLowerCase();

        if (keyMatch && metaMatch && ctrlMatch && shiftMatch && altMatch) {
          e.preventDefault();
          shortcut.callback();
          break; // Only trigger first matching shortcut
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [shortcuts]);
}

/**
 * Pre-configured shortcuts for Kanban AI
 *
 * @example
 * ```tsx
 * function App() {
 *   const [commandOpen, setCommandOpen] = useState(false);
 *   const [view, setView] = useState<ViewMode>('board');
 *
 *   useKanbanShortcuts({
 *     onToggleCommandPalette: () => setCommandOpen((o) => !o),
 *     onCreateTicket: () => openCreateTicketModal(),
 *     onOpenAI: () => openAIChat(),
 *     onSwitchView: setView,
 *   });
 * }
 * ```
 */
export function useKanbanShortcuts(handlers: {
  onToggleCommandPalette: () => void;
  onCreateTicket: () => void;
  onOpenAI: () => void;
  onDailySummary?: () => void;
  onSwitchView: (view: 'board' | 'list' | 'timeline') => void;
  onOpenSettings?: () => void;
  onToggleSidebar?: () => void;
}) {
  useKeyboardShortcuts([
    // Command palette
    {
      key: 'k',
      metaKey: true,
      callback: handlers.onToggleCommandPalette,
    },

    // Actions
    {
      key: 'n',
      metaKey: true,
      callback: handlers.onCreateTicket,
    },
    {
      key: 'a',
      metaKey: true,
      shiftKey: true,
      callback: handlers.onOpenAI,
    },
    {
      key: 's',
      metaKey: true,
      shiftKey: true,
      callback: handlers.onDailySummary || (() => {}),
    },

    // Navigation
    {
      key: '1',
      metaKey: true,
      callback: () => handlers.onSwitchView('board'),
    },
    {
      key: '2',
      metaKey: true,
      callback: () => handlers.onSwitchView('list'),
    },
    {
      key: '3',
      metaKey: true,
      callback: () => handlers.onSwitchView('timeline'),
    },

    // Settings
    {
      key: ',',
      metaKey: true,
      callback: handlers.onOpenSettings || (() => {}),
    },

    // Sidebar
    {
      key: '/',
      metaKey: true,
      callback: handlers.onToggleSidebar || (() => {}),
    },
  ]);
}
