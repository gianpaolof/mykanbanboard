import { useEffect, useState, useCallback, useMemo } from 'react';
import { toast } from 'sonner';
import { KanbanBoard } from '@/components/kanban/KanbanBoard';
import { CalendarView } from '@/components/calendar';
import { CreateTicketModal } from '@/components/kanban/CreateTicketModal';
import { Sidebar } from '@/components/layout/Sidebar';
import { Header } from '@/components/layout/Header';
import { CommandPalette } from '@/components/layout/CommandPalette';
import { AgentChat } from '@/components/ai/AgentChat';
import { SettingsModal } from '@/components/settings/SettingsModal';
import { CreateBoardModal } from '@/components/boards/CreateBoardModal';
import { Toaster } from '@/components/ui/Toaster';
import { useBoardStore, filterTickets } from '@/stores/boardStore';
import { useThemeStore } from '@/stores/themeStore';
import { useKanbanShortcuts } from '@/hooks/useKeyboardShortcuts';
import type { FilterConfig } from '@/types';

function App() {
  const loadBoard = useBoardStore((state) => state.loadBoard);
  const isLoading = useBoardStore((state) => state.isLoading);
  const tickets = useBoardStore((state) => state.tickets);

  // UI State
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);
  const [aiPanelOpen, setAiPanelOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [createTicketOpen, setCreateTicketOpen] = useState(false);
  const [createBoardOpen, setCreateBoardOpen] = useState(false);
  const [createTicketColumnId, setCreateTicketColumnId] = useState<string | undefined>(undefined);
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [_sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [currentView, setCurrentView] = useState<'board' | 'list' | 'timeline' | 'calendar'>('board');
  const [filter, setFilter] = useState<FilterConfig>({});

  // Apply filtering to tickets
  const filteredTickets = useMemo(
    () => filterTickets(tickets, filter),
    [tickets, filter]
  );

  // Count total tickets (from filtered)
  const ticketCount = Object.values(tickets).flat().length;

  // Initialize theme on mount
  const initializeTheme = useThemeStore((state) => state.initializeTheme);

  useEffect(() => {
    initializeTheme();
  }, [initializeTheme]);

  // Load board on mount
  useEffect(() => {
    loadBoard();
  }, [loadBoard]);

  // Handlers
  const handleCreateTicket = useCallback((columnId?: string) => {
    setCreateTicketColumnId(columnId);
    setCreateTicketOpen(true);
  }, []);

  const handleOpenAI = useCallback(() => {
    setCommandPaletteOpen(false);
    setAiPanelOpen(true);
  }, []);

  const handleSwitchView = useCallback((view: 'board' | 'list' | 'timeline' | 'calendar') => {
    setCurrentView(view);
    if (view !== 'board' && view !== 'calendar') {
      toast.info(`${view.charAt(0).toUpperCase() + view.slice(1)} view coming soon`);
    }
  }, []);

  const handleToggleSidebar = useCallback(() => {
    setSidebarCollapsed((prev) => !prev);
  }, []);

  const handleDailySummary = useCallback(() => {
    toast.info('Daily summary coming soon');
  }, []);

  const handleSettings = useCallback(() => {
    setSettingsOpen(true);
  }, []);

  const handleFilterChange = useCallback((newFilter: FilterConfig) => {
    setFilter(newFilter);
  }, []);

  // Use centralized keyboard shortcuts hook
  useKanbanShortcuts({
    onToggleCommandPalette: () => setCommandPaletteOpen((prev) => !prev),
    onCreateTicket: () => handleCreateTicket(),
    onOpenAI: () => setAiPanelOpen((prev) => !prev),
    onDailySummary: handleDailySummary,
    onSwitchView: handleSwitchView,
    onOpenSettings: handleSettings,
    onToggleSidebar: handleToggleSidebar,
  });

  // Handle escape to close modals (not handled by useKanbanShortcuts)
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setCommandPaletteOpen(false);
        setAiPanelOpen(false);
        setSettingsOpen(false);
        setCreateTicketOpen(false);
        setCreateBoardOpen(false);
      }
    };
    window.addEventListener('keydown', handleEscape);
    return () => window.removeEventListener('keydown', handleEscape);
  }, []);


  if (isLoading) {
    return (
      <div className="h-screen w-screen flex items-center justify-center bg-bg-primary">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin" />
          <div className="text-text-tertiary text-sm">Loading board...</div>
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
          ticketCount={ticketCount}
          onAIClick={() => setAiPanelOpen(true)}
          onSettingsClick={handleSettings}
          onViewChange={handleSwitchView}
          filter={filter}
          onFilterChange={handleFilterChange}
          onCreateBoard={() => setCreateBoardOpen(true)}
        />

        {/* Main Content */}
        <main className="flex-1 overflow-hidden">
          {currentView === 'calendar' ? (
            <CalendarView filteredTickets={filteredTickets} />
          ) : (
            <KanbanBoard
              onAddTicket={handleCreateTicket}
              filteredTickets={filteredTickets}
            />
          )}
        </main>
      </div>

      {/* Command Palette */}
      <CommandPalette
        open={commandPaletteOpen}
        onOpenChange={setCommandPaletteOpen}
        onCreateTicket={() => handleCreateTicket()}
        onOpenAI={handleOpenAI}
        onSwitchView={handleSwitchView}
      />

      {/* AI Chat */}
      <AgentChat
        isOpen={aiPanelOpen}
        onClose={() => setAiPanelOpen(false)}
      />

      {/* Settings Modal */}
      <SettingsModal
        open={settingsOpen}
        onClose={() => setSettingsOpen(false)}
      />

      {/* Create Ticket Modal */}
      <CreateTicketModal
        isOpen={createTicketOpen}
        onClose={() => setCreateTicketOpen(false)}
        defaultColumnId={createTicketColumnId}
      />

      {/* Create Board Modal */}
      <CreateBoardModal
        isOpen={createBoardOpen}
        onClose={() => setCreateBoardOpen(false)}
      />

      {/* Toast Notifications */}
      <Toaster />
    </div>
  );
}

export default App;
