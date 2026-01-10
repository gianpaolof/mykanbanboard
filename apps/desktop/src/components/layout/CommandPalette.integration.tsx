/**
 * Complete CommandPalette Integration Example
 *
 * This shows the recommended way to integrate the CommandPalette
 * into your main App component with global keyboard shortcuts.
 */

import { useState } from 'react';
import { CommandPalette } from './CommandPalette';
import { useKanbanShortcuts } from '../../hooks/useKeyboardShortcuts';
import type { ViewMode } from '../../types';

export function AppLayout() {
  // UI State
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);
  const [currentView, setCurrentView] = useState<ViewMode>('board');

  // Global keyboard shortcuts
  useKanbanShortcuts({
    // Toggle command palette with ⌘K
    onToggleCommandPalette: () => setCommandPaletteOpen((prev) => !prev),

    // Create ticket with ⌘N
    onCreateTicket: handleCreateTicket,

    // Open AI with ⌘⇧A
    onOpenAI: handleOpenAI,

    // Daily summary with ⌘⇧S
    onDailySummary: handleDailySummary,

    // Switch views with ⌘1/2/3
    onSwitchView: handleSwitchView,

    // Open settings with ⌘,
    onOpenSettings: handleOpenSettings,

    // Toggle sidebar with ⌘/
    onToggleSidebar: handleToggleSidebar,
  });

  // Command handlers
  function handleCreateTicket() {
    console.log('Creating new ticket...');
    // TODO: Open ticket creation modal
    // Example:
    // setTicketModalOpen(true);
    // setTicketModalMode('create');
  }

  function handleOpenAI() {
    console.log('Opening AI assistant...');
    // TODO: Open AI chat panel
    // Example:
    // setAIChatOpen(true);
  }

  function handleDailySummary() {
    console.log('Generating daily summary...');
    // TODO: Generate and show daily summary
    // Example:
    // const summary = await agentAPI.getDailySummary();
    // showNotification(summary);
  }

  function handleSwitchView(view: ViewMode) {
    console.log('Switching to view:', view);
    setCurrentView(view);
    // TODO: Update your view state/store
    // Example:
    // useAppStore.setState({ currentView: view });
  }

  function handleOpenSettings() {
    console.log('Opening settings...');
    // TODO: Open settings modal
    // Example:
    // setSettingsOpen(true);
  }

  function handleToggleSidebar() {
    console.log('Toggling sidebar...');
    // TODO: Toggle sidebar visibility
    // Example:
    // setSidebarCollapsed((prev) => !prev);
  }

  return (
    <div className="min-h-screen bg-bg-primary">
      {/* App Header */}
      <header className="border-b border-border px-6 py-4">
        <div className="flex items-center justify-between">
          <h1 className="font-display text-xl font-semibold text-zinc-100">Kanban AI</h1>

          <div className="flex items-center gap-2">
            <kbd className="rounded bg-bg-tertiary px-2 py-1 font-mono text-xs text-zinc-400">
              ⌘K
            </kbd>
            <span className="text-sm text-zinc-500">Open command palette</span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="p-6">
        <div className="rounded-xl border border-border bg-bg-secondary p-8">
          <h2 className="text-lg font-semibold text-zinc-100">Current View: {currentView}</h2>
          <p className="mt-2 text-zinc-400">
            Press <kbd className="rounded bg-bg-tertiary px-1.5 py-0.5 font-mono text-xs">⌘K</kbd>{' '}
            to open the command palette and navigate your workspace.
          </p>

          <div className="mt-6 space-y-2 text-sm text-zinc-500">
            <div className="flex items-center gap-3">
              <kbd className="rounded bg-bg-tertiary px-2 py-1 font-mono text-xs">⌘N</kbd>
              <span>Create new ticket</span>
            </div>
            <div className="flex items-center gap-3">
              <kbd className="flex gap-0.5 rounded bg-bg-tertiary px-2 py-1 font-mono text-xs">
                <span>⌘</span>
                <span>⇧</span>
                <span>A</span>
              </kbd>
              <span>Ask AI assistant</span>
            </div>
            <div className="flex items-center gap-3">
              <kbd className="rounded bg-bg-tertiary px-2 py-1 font-mono text-xs">⌘1/2/3</kbd>
              <span>Switch views</span>
            </div>
          </div>
        </div>
      </main>

      {/* Command Palette */}
      <CommandPalette
        open={commandPaletteOpen}
        onOpenChange={setCommandPaletteOpen}
        onCreateTicket={handleCreateTicket}
        onOpenAI={handleOpenAI}
        onSwitchView={handleSwitchView}
      />
    </div>
  );
}

/**
 * Alternative: Minimal integration without keyboard shortcuts hook
 */
export function MinimalAppLayout() {
  const [commandOpen, setCommandOpen] = useState(false);

  return (
    <>
      <div className="min-h-screen bg-bg-primary p-8">
        <button
          onClick={() => setCommandOpen(true)}
          className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white hover:bg-accent-hover"
        >
          Open Command Palette
        </button>
      </div>

      <CommandPalette
        open={commandOpen}
        onOpenChange={setCommandOpen}
        onCreateTicket={() => console.log('Create ticket')}
        onOpenAI={() => console.log('Open AI')}
        onSwitchView={(view) => console.log('Switch to', view)}
      />
    </>
  );
}
