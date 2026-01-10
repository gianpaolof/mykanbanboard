import { useState } from 'react';
import {
  Zap,
  LayoutGrid,
  List,
  Calendar,
  Inbox,
  User,
  Clock,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useBoardStore } from '@/stores/boardStore';

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
// SIDEBAR COMPONENT
// ===========================================

export function Sidebar() {
  const labels = useBoardStore((state) => state.labels);
  const [activeView, setActiveView] = useState<NavItemType>('board');
  const [activeFilter, setActiveFilter] = useState<FilterItemType | null>(null);

  return (
    <aside className="w-64 h-screen bg-[#18181b] border-r border-[rgba(255,255,255,0.06)] flex flex-col">
      {/* Logo Section */}
      <div className="p-4 border-b border-[rgba(255,255,255,0.06)]">
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
            <h1 className="text-sm font-semibold text-white font-display">
              Kanban AI
            </h1>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <div className="flex-1 overflow-y-auto">
        {/* Views Section */}
        <div className="px-3 py-4">
          <h2 className="px-2 mb-2 text-2xs font-medium text-zinc-500 uppercase tracking-wider">
            Views
          </h2>
          <nav className="space-y-1">
            {NAV_ITEMS.map((item) => {
              const Icon = item.icon;
              const isActive = activeView === item.id;

              return (
                <button
                  key={item.id}
                  onClick={() => setActiveView(item.id)}
                  className={cn(
                    'w-full flex items-center gap-2.5 px-2.5 py-2 rounded-md text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-[rgba(99,102,241,0.15)] text-indigo-400'
                      : 'text-zinc-400 hover:bg-[rgba(255,255,255,0.05)] hover:text-zinc-300'
                  )}
                >
                  <Icon className="w-4 h-4" />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>
        </div>

        {/* Filters Section */}
        <div className="px-3 py-4 border-t border-[rgba(255,255,255,0.06)]">
          <h2 className="px-2 mb-2 text-2xs font-medium text-zinc-500 uppercase tracking-wider">
            Filters
          </h2>
          <nav className="space-y-1">
            {FILTER_ITEMS.map((item) => {
              const Icon = item.icon;
              const isActive = activeFilter === item.id;

              return (
                <button
                  key={item.id}
                  onClick={() => setActiveFilter(isActive ? null : item.id)}
                  className={cn(
                    'w-full flex items-center gap-2.5 px-2.5 py-2 rounded-md text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-[rgba(99,102,241,0.15)] text-indigo-400'
                      : 'text-zinc-400 hover:bg-[rgba(255,255,255,0.05)] hover:text-zinc-300'
                  )}
                >
                  <Icon className="w-4 h-4" />
                  <span className="flex-1 text-left">{item.label}</span>
                  {item.badge !== undefined && (
                    <span
                      className={cn(
                        'px-1.5 py-0.5 text-2xs font-semibold rounded-md',
                        isActive
                          ? 'bg-indigo-500/20 text-indigo-400'
                          : 'bg-zinc-800 text-zinc-400'
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

        {/* Labels Section */}
        <div className="px-3 py-4 border-t border-[rgba(255,255,255,0.06)]">
          <h2 className="px-2 mb-2 text-2xs font-medium text-zinc-500 uppercase tracking-wider">
            Labels
          </h2>
          <nav className="space-y-1">
            {labels.map((label) => (
              <button
                key={label.id}
                className="w-full flex items-center gap-2.5 px-2.5 py-2 rounded-md text-sm font-medium text-zinc-400 hover:bg-[rgba(255,255,255,0.05)] hover:text-zinc-300 transition-colors"
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
  );
}
