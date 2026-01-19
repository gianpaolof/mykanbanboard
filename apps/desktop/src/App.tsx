import { useEffect, useState, useCallback, useMemo } from 'react';
import { toast } from 'sonner';
import { KanbanBoard } from '@/components/kanban/KanbanBoard';
import { CalendarView } from '@/components/calendar';
import { CreateTicketModal } from '@/components/kanban/CreateTicketModal';
import { Sidebar } from '@/components/layout/Sidebar';
import { Header } from '@/components/layout/Header';
import { CommandPalette } from '@/components/layout/CommandPalette';
import { AgentChat, AgentStatsPanel } from '@/components/ai';
import { SettingsModal } from '@/components/settings/SettingsModal';
import { ProjectWizard } from '@/components/settings/ProjectWizard';
import { CreateBoardModal } from '@/components/boards/CreateBoardModal';
import { Toaster } from '@/components/ui/Toaster';
import { useBoardStore, filterTickets } from '@/stores/boardStore';
import { useProjectStore } from '@/stores/projectStore';
import { useThemeStore } from '@/stores/themeStore';
import { useKanbanShortcuts } from '@/hooks/useKeyboardShortcuts';
import { api, type DailySummaryTicket } from '@/lib/tauri';
import type { FilterConfig, Ticket } from '@/types';

function App() {
  const loadBoard = useBoardStore((state) => state.loadBoard);
  const isLoading = useBoardStore((state) => state.isLoading);
  const tickets = useBoardStore((state) => state.tickets);
  const columns = useBoardStore((state) => state.columns);
  const currentBoardId = useBoardStore((state) => state.currentBoardId);

  // Project wizard state
  const showWizard = useProjectStore((state) => state.showWizard);
  const closeWizard = useProjectStore((state) => state.closeWizard);
  const isWizardCompleted = useProjectStore((state) => state.isWizardCompleted);
  const openWizard = useProjectStore((state) => state.openWizard);

  // UI State
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);
  const [aiPanelOpen, setAiPanelOpen] = useState(false);
  const [statsPanelOpen, setStatsPanelOpen] = useState(false);
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

  // Check if wizard should be shown for first-time users
  useEffect(() => {
    if (currentBoardId && !isLoading && !isWizardCompleted(currentBoardId)) {
      // Show wizard if board has never been configured
      openWizard();
    }
  }, [currentBoardId, isLoading, isWizardCompleted, openWizard]);

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

  const handleDailySummary = useCallback(async () => {
    // Helper to convert ticket to DailySummaryTicket format
    const toSummaryTicket = (ticket: Ticket): DailySummaryTicket => ({
      id: ticket.id,
      title: ticket.title,
      description: ticket.description,
      priority: ticket.priority,
      labels: ticket.labels.map((l) => l.name),
      due_date: ticket.dueDate,
      column_id: ticket.columnId,
    });

    // Categorize tickets by column name patterns
    const allTickets = Object.values(tickets).flat();

    // Find columns by name patterns
    const inProgressColIds = columns
      .filter((c) => /in.?progress|doing|working|active/i.test(c.name))
      .map((c) => c.id);
    const blockedColIds = columns
      .filter((c) => /block|stuck|waiting|on.?hold/i.test(c.name))
      .map((c) => c.id);
    const doneColIds = columns
      .filter((c) => /done|complete|finish|closed/i.test(c.name))
      .map((c) => c.id);

    // Categorize tickets
    const inProgress = allTickets
      .filter((t) => inProgressColIds.includes(t.columnId))
      .map(toSummaryTicket);

    const blocked = allTickets
      .filter((t) => blockedColIds.includes(t.columnId))
      .map(toSummaryTicket);

    // Due soon = tickets with due date in next 3 days (not done)
    const now = new Date();
    const threeDaysFromNow = new Date(now.getTime() + 3 * 24 * 60 * 60 * 1000);
    const dueSoon = allTickets
      .filter((t) => {
        if (!t.dueDate || doneColIds.includes(t.columnId)) return false;
        const due = new Date(t.dueDate);
        return due >= now && due <= threeDaysFromNow;
      })
      .map(toSummaryTicket);

    // Recently completed = done in last 24 hours (if we had updatedAt, use that)
    // For now, just take last 5 from done columns
    const recentlyCompleted = allTickets
      .filter((t) => doneColIds.includes(t.columnId))
      .slice(-5)
      .map(toSummaryTicket);

    // Show loading toast
    const loadingToast = toast.loading('Generating daily summary...');

    try {
      const result = await api.agent.dailySummary({
        in_progress: inProgress,
        blocked: blocked,
        due_soon: dueSoon,
        recently_completed: recentlyCompleted,
      });

      toast.dismiss(loadingToast);

      // Show summary in a nice toast
      const summaryMessage = [
        result.greeting,
        '',
        result.focus_today.length > 0 ? `Focus today: ${result.focus_today.join(', ')}` : '',
        result.blockers.length > 0 ? `Blockers: ${result.blockers.join(', ')}` : '',
        result.quick_wins.length > 0 ? `Quick wins: ${result.quick_wins.join(', ')}` : '',
      ].filter(Boolean).join('\n');

      toast.success(summaryMessage, {
        duration: 10000,
        style: { whiteSpace: 'pre-line' },
      });
    } catch (error) {
      toast.dismiss(loadingToast);
      console.error('Daily summary failed:', error);
      toast.error('Failed to generate daily summary. Make sure the AI agent is running.');
    }
  }, [tickets, columns]);

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
        setStatsPanelOpen(false);
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
      <div className="h-full w-full flex items-center justify-center bg-bg-primary">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin" />
          <div className="text-text-tertiary text-sm">Loading board...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full w-full overflow-hidden bg-bg-primary flex">
      {/* Sidebar */}
      <Sidebar />

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <Header
          ticketCount={ticketCount}
          onAIClick={() => setAiPanelOpen(true)}
          onStatsClick={() => setStatsPanelOpen(true)}
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

      {/* Agent Stats Panel */}
      <AgentStatsPanel
        open={statsPanelOpen}
        onClose={() => setStatsPanelOpen(false)}
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

      {/* Project Setup Wizard */}
      <ProjectWizard
        open={showWizard}
        onClose={closeWizard}
      />

      {/* Toast Notifications */}
      <Toaster />
    </div>
  );
}

export default App;
