import { useEffect, useState, useCallback } from 'react';
import { KanbanBoard } from '@/components/kanban/KanbanBoard';
import { Sidebar } from '@/components/layout/Sidebar';
import { Header } from '@/components/layout/Header';
import { CommandPalette } from '@/components/layout/CommandPalette';
import { AgentChat } from '@/components/ai/AgentChat';
import { useBoardStore } from '@/stores/boardStore';

function App() {
  const loadBoard = useBoardStore((state) => state.loadBoard);
  const isLoading = useBoardStore((state) => state.isLoading);
  const tickets = useBoardStore((state) => state.tickets);

  // UI State
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);
  const [aiPanelOpen, setAiPanelOpen] = useState(false);

  // Count total tickets
  const ticketCount = Object.values(tickets).flat().length;

  // Load board on mount
  useEffect(() => {
    loadBoard();
  }, [loadBoard]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Cmd/Ctrl + K - Command Palette
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setCommandPaletteOpen((prev) => !prev);
      }

      // Cmd/Ctrl + Shift + A - AI Panel
      if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key === 'a') {
        e.preventDefault();
        setAiPanelOpen((prev) => !prev);
      }

      // Escape - Close modals
      if (e.key === 'Escape') {
        setCommandPaletteOpen(false);
        setAiPanelOpen(false);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Handlers
  const handleCreateTicket = useCallback(() => {
    console.log('Create ticket');
    // TODO: Open create ticket modal
  }, []);

  const handleOpenAI = useCallback(() => {
    setCommandPaletteOpen(false);
    setAiPanelOpen(true);
  }, []);

  const handleSwitchView = useCallback((view: 'board' | 'list' | 'timeline') => {
    console.log('Switch to view:', view);
    // TODO: Implement view switching
  }, []);


  if (isLoading) {
    return (
      <div className="h-screen w-screen flex items-center justify-center bg-bg-primary">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin" />
          <div className="text-zinc-500 text-sm">Loading board...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen w-screen overflow-hidden bg-bg-primary flex">
      {/* Sidebar */}
      <Sidebar />

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <Header
          boardTitle="My Project"
          ticketCount={ticketCount}
          lastUpdated="2m ago"
          onSearchClick={() => setCommandPaletteOpen(true)}
          onAIClick={() => setAiPanelOpen(true)}
          onSettingsClick={() => console.log('Settings')}
          onViewChange={handleSwitchView}
        />

        {/* Board */}
        <main className="flex-1 overflow-hidden">
          <KanbanBoard />
        </main>
      </div>

      {/* Command Palette */}
      <CommandPalette
        open={commandPaletteOpen}
        onOpenChange={setCommandPaletteOpen}
        onCreateTicket={handleCreateTicket}
        onOpenAI={handleOpenAI}
        onSwitchView={handleSwitchView}
      />

      {/* AI Chat */}
      <AgentChat
        isOpen={aiPanelOpen}
        onClose={() => setAiPanelOpen(false)}
      />
    </div>
  );
}

export default App;
