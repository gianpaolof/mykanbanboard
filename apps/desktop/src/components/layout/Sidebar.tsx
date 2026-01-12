import { useState, useCallback, useMemo, memo, useRef, useEffect } from 'react';
import {
  Zap,
  LayoutGrid,
  List,
  Calendar,
  Inbox,
  User,
  Clock,
  Plus,
  GripVertical,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useBoardStore, selectBoards } from '@/stores/boardStore';
import { BoardItem, CreateBoardModal } from '@/components/boards';
import type { Ticket } from '@/types';

// ===========================================
// RESIZE CONSTANTS
// ===========================================

const MIN_WIDTH = 200;
const MAX_WIDTH = 400;
const DEFAULT_WIDTH = 256; // w-64
const STORAGE_KEY = 'kanban-sidebar-width';

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

// Helper to count tickets due within next 7 days
const countDueSoon = (tickets: Ticket[]): number => {
  const now = new Date();
  const weekFromNow = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000);
  return tickets.filter((t) => {
    if (!t.dueDate) return false;
    const due = new Date(t.dueDate);
    return due >= now && due <= weekFromNow;
  }).length;
};

// Helper to count tickets assigned to current user
// TODO: Implement when user/assignee system is added to Ticket type
const countMyTickets = (_tickets: Ticket[]): number => {
  // No assignee field exists yet - return 0 until implemented
  return 0;
};

const createFilterItems = (allTickets: Ticket[]): FilterItem[] => [
  { id: 'all', label: 'All Tickets', icon: Inbox, badge: allTickets.length },
  { id: 'my', label: 'My Tickets', icon: User, badge: countMyTickets(allTickets) },
  { id: 'due-soon', label: 'Due Soon', icon: Clock, badge: countDueSoon(allTickets) },
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
  filterItems: FilterItem[];
}

const FiltersSection = memo(function FiltersSection({
  activeFilter,
  onFilterChange,
  filterItems,
}: FiltersSectionProps) {
  return (
    <div className="px-3 py-4 border-t border-sidebar-border">
      <h2 className="px-2 mb-2 text-2xs font-medium text-text-muted uppercase tracking-wider">
        Filters
      </h2>
      <nav className="space-y-1">
        {filterItems.map((item) => {
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
  const tickets = useBoardStore((state) => state.tickets);

  // Flatten all tickets for counting
  const allTickets = useMemo(() => {
    return Object.values(tickets).flat();
  }, [tickets]);

  // Create filter items with dynamic counts
  const filterItems = useMemo(() => {
    return createFilterItems(allTickets);
  }, [allTickets]);

  const [activeView, setActiveView] = useState<NavItemType>('board');
  const [activeFilter, setActiveFilter] = useState<FilterItemType | null>(null);
  const [isCreateBoardOpen, setIsCreateBoardOpen] = useState(false);

  // Resize state
  const [width, setWidth] = useState(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    return saved ? parseInt(saved, 10) : DEFAULT_WIDTH;
  });
  const [isResizing, setIsResizing] = useState(false);
  const sidebarRef = useRef<HTMLElement>(null);

  // Save width to localStorage when it changes
  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, width.toString());
  }, [width]);

  // Handle resize
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizing(true);
  }, []);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing) return;
      const newWidth = Math.min(MAX_WIDTH, Math.max(MIN_WIDTH, e.clientX));
      setWidth(newWidth);
    };

    const handleMouseUp = () => {
      setIsResizing(false);
    };

    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };
  }, [isResizing]);

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
      <aside
        ref={sidebarRef}
        style={{ width }}
        className="relative h-full bg-sidebar-bg border-r border-sidebar-border flex flex-col flex-shrink-0"
      >
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
            filterItems={filterItems}
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

        {/* Resize handle */}
        <div
          onMouseDown={handleMouseDown}
          className={cn(
            'absolute top-0 right-0 w-1 h-full cursor-col-resize group',
            'hover:bg-indigo-500/50 transition-colors',
            isResizing && 'bg-indigo-500'
          )}
        >
          {/* Visual indicator on hover */}
          <div
            className={cn(
              'absolute top-1/2 -translate-y-1/2 -right-1 opacity-0 group-hover:opacity-100 transition-opacity',
              isResizing && 'opacity-100'
            )}
          >
            <GripVertical className="w-3 h-3 text-text-muted" />
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
