/**
 * CommandPalette Usage Example
 *
 * This example shows how to integrate the CommandPalette component
 * into your main application layout.
 */

import { useState, useEffect } from 'react';
import { CommandPalette } from './CommandPalette';

export function AppWithCommandPalette() {
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);

  // Global keyboard shortcut to open command palette
  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setCommandPaletteOpen((open) => !open);
      }
    };

    document.addEventListener('keydown', down);
    return () => document.removeEventListener('keydown', down);
  }, []);

  const handleCreateTicket = () => {
    console.log('Creating new ticket...');
    // Open ticket creation modal/dialog
  };

  const handleOpenAI = () => {
    console.log('Opening AI assistant...');
    // Open AI chat panel/modal
  };

  const handleSwitchView = (view: 'board' | 'list' | 'timeline') => {
    console.log('Switching to view:', view);
    // Update view state in your app
  };

  return (
    <div className="min-h-screen bg-bg-primary">
      {/* Your app content */}
      <div className="p-8">
        <h1 className="text-2xl font-bold text-zinc-100">Kanban AI</h1>
        <p className="mt-2 text-zinc-400">
          Press <kbd className="rounded bg-bg-tertiary px-2 py-1 font-mono text-xs">⌘K</kbd> to
          open command palette
        </p>
      </div>

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
