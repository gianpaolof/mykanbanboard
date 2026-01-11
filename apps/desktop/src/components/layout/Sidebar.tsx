import { useState, useCallback, useMemo, memo } from 'react';
import {
  Zap,
  LayoutGrid,
  List,
  Calendar,
  Inbox,
  User,
  Clock,
  Plus,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useBoardStore, selectBoards } from '@/stores/boardStore';
import { BoardItem, CreateBoardModal } from '@/components/boards';

// ===========================================
// TYPES
// ===========================================

type NavItemType = 'board' | 'list' | 'timeline';
type FilterItemType = 'all' | 'my' | 'due-soon';

interface NavItem {
  id: NavItemType;
  label: string;
  icon: typeof LayoutGrid;
}

interface FilterItem {
  id: FilterItemType;
  label: string;
  icon: typeof Inbox;
  badge?: number;
}

// ===========================================
// CONSTANTS
// ===========================================

const NAV_ITEMS: NavItem[] = [
  { id: 'board', label: 'Board', icon: LayoutGrid },
  { id: 'list', label: 'List', icon: List },
  { id: 'timeline', label: 'Timeline', icon: Calendar },
];

const FILTER_ITEMS: FilterItem[] = [
  { id: 'all', label: 'All Tickets', icon: Inbox, badge: 24 },
  { id: 'my', label: 'My Tickets', icon: User, badge: 8 },
  { id: 'due-soon', label: 'Due Soon', icon: Clock, badge: 3 },
];

// ===========================================
// MEMOIZED SECTIONS
// ===========================================

const LogoSection = memo(function LogoSection() {
  return (
    <div className="p-4 border-b border-sidebar-border">
      <div className="flex items-center gap-3">
        {/* Logo with gradient */}
        <div className="relative">
          <div className="absolute inset-0 bg-gradient-to-br from-indigo-500 to-purple-500 rounded-lg blur-md opacity-50" />
          <div className="relative w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-500 rounded-lg flex items-center justify-center shadow-lg shadow-indigo-500/30">
            <Zap className="w-5 h-5 text-white" fill="white" />
          </div>
        </div>

        {/* Workspace name */}
        <div>
          <h1 className="text-sm font-semibold text-text-primary font-display">
            Kanban AI
          </h1>
        </div>
      </div>
    </div>
  );
});

interface ViewsSectionProps {
  activeView: NavItemType;
  onViewChange: (view: NavItemType) => void;
}

const ViewsSection = memo(function ViewsSection({
  activeView,
  onViewChange,
}: ViewsSectionProps) {
  return (
    <div className="px-3 py-4">
      <h2 className="px-2 mb-2 text-2xs font-medium text-text-muted uppercase tracking-wider">
        Views
      </h2>
      <nav className="space-y-1">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = activeView === item.id;

          return (
            <button
              key={item.id}
              onClick={() => onViewChange(item.id)}
              className={cn(
                'w-full flex items-center gap-2.5 px-2.5 py-2 rounded-md text-sm font-medium transition-colors',
                isActive
                  ? 'bg-accent-muted text-indigo-500 dark:text-indigo-400'
                  : 'text-text-tertiary hover:bg-bg-hover hover:text-text-secondary'
              )}
            >
              <Icon className="w-4 h-4" />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>
    </div>
  );
});

interface FiltersSectionProps {
  activeFilter: FilterItemType | null;
  onFilterChange: (filter: FilterItemType | null) => void;
}

const FiltersSection = memo(function FiltersSection({
  activeFilter,
  onFilterChange,
}: FiltersSectionProps) {
  return (
    <div className="px-3 py-4 border-t border-sidebar-border">
      <h2 className="px-2 mb-2 text-2xs font-medium text-text-muted uppercase tracking-wider">
        Filters
      </h2>
      <nav className="space-y-1">
        {FILTER_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = activeFilter === item.id;

          return (
            <button
              key={item.id}
              onClick={() => onFilterChange(isActive ? null : item.id)}
              className={cn(
                'w-full flex items-center gap-2.5 px-2.5 py-2 rounded-md text-sm font-medium transition-colors',
                isActive
                  ? 'bg-accent-muted text-indigo-500 dark:text-indigo-400'
                  : 'text-text-tertiary hover:bg-bg-hover hover:text-text-secondary'
              )}
            >
              <Icon className="w-4 h-4" />
              <span className="flex-1 text-left">{item.label}</span>
              {item.badge !== undefined && (
                <span
                  className={cn(
                    'px-1.5 py-0.5 text-2xs font-semibold rounded-md',
                    isActive
                      ? 'bg-indigo-500/20 text-indigo-500 dark:text-indigo-400'
                      : 'bg-bg-tertiary text-text-tertiary'
                  )}
                >
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>
    </div>
  );
});

// ===========================================
// SIDEBAR COMPONENT
// ===========================================

export function Sidebar() {
  const boards = useBoardStore(selectBoards);
  const currentBoardId = useBoardStore((state) => state.currentBoardId);
  const switchBoard = useBoardStore((state) => state.switchBoard);
  const labels = useBoardStore((state) => state.labels);

  const [activeView, setActiveView] = useState<NavItemType>('board');
  const [activeFilter, setActiveFilter] = useState<FilterItemType | null>(null);
  const [isCreateBoardOpen, setIsCreateBoardOpen] = useState(false);

  const handleViewChange = useCallback((view: NavItemType) => {
    setActiveView(view);
  }, []);

  const handleFilterChange = useCallback((filter: FilterItemType | null) => {
    setActiveFilter(filter);
  }, []);

  const handleSelectBoard = useCallback(
    (boardId: string) => {
      switchBoard(boardId);
    },
    [switchBoard]
  );

  const handleOpenCreateBoard = useCallback(() => {
    setIsCreateBoardOpen(true);
  }, []);

  const handleCloseCreateBoard = useCallback(() => {
    setIsCreateBoardOpen(false);
  }, []);

  // Memoize sorted boards
  const sortedBoards = useMemo(
    () => [...boards].sort((a, b) => a.name.localeCompare(b.name)),
    [boards]
  );

  return (
    <>
      <aside className="w-64 h-screen bg-sidebar-bg border-r border-sidebar-border flex flex-col">
        <LogoSection />

        {/* Navigation */}
        <div className="flex-1 overflow-y-auto">
          {/* Boards Section */}
          <div className="px-3 py-4 border-b border-sidebar-border">
            <div className="flex items-center justify-between px-2 mb-2">
              <h2 className="text-2xs font-medium text-text-muted uppercase tracking-wider">
                Boards
              </h2>
              <button
                onClick={handleOpenCreateBoard}
                className="p-1 rounded text-text-muted hover:text-text-secondary hover:bg-bg-hover transition-colors"
                title="Create new board"
              >
                <Plus className="w-3.5 h-3.5" />
              </button>
            </div>
            <nav className="space-y-0.5">
              {sortedBoards.map((board) => (
                <BoardItem
                  key={board.id}
                  board={board}
                  isActive={board.id === currentBoardId}
                  onSelect={() => handleSelectBoard(board.id)}
                />
              ))}
            </nav>
          </div>

          {/* Views Section */}
          <ViewsSection activeView={activeView} onViewChange={handleViewChange} />

          {/* Filters Section */}
          <FiltersSection
            activeFilter={activeFilter}
            onFilterChange={handleFilterChange}
          />

          {/* Labels Section */}
          <div className="px-3 py-4 border-t border-sidebar-border">
            <h2 className="px-2 mb-2 text-2xs font-medium text-text-muted uppercase tracking-wider">
              Labels
            </h2>
            <nav className="space-y-1">
              {labels.map((label) => (
                <button
                  key={label.id}
                  className="w-full flex items-center gap-2.5 px-2.5 py-2 rounded-md text-sm font-medium text-text-tertiary hover:bg-bg-hover hover:text-text-secondary transition-colors"
                >
                  <span
                    className="w-2 h-2 rounded-full"
                    style={{ backgroundColor: label.color }}
                  />
                  <span>{label.name}</span>
                </button>
              ))}
            </nav>
          </div>
        </div>
      </aside>

      {/* Create Board Modal */}
      <CreateBoardModal
        isOpen={isCreateBoardOpen}
        onClose={handleCloseCreateBoard}
      />
    </>
  );
}
