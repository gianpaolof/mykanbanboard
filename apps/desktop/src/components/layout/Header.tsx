// components/layout/Header.tsx
import { useState, memo } from 'react';
import {
  LayoutGrid,
  List,
  GanttChart,
  Calendar,
  Sparkles,
  Settings,
  BarChart3,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { ThemeToggle } from '@/components/ui/ThemeToggle';
import { SearchFilterBar } from '@/components/kanban/SearchFilterBar';
import { BoardSwitcher } from '@/components/boards/BoardSwitcher';
import type { FilterConfig } from '@/types';

type ViewMode = 'board' | 'list' | 'timeline' | 'calendar';

interface HeaderProps {
  ticketCount?: number;
  lastUpdated?: string;
  onAIClick?: () => void;
  onStatsClick?: () => void;
  onSettingsClick?: () => void;
  onViewChange?: (view: ViewMode) => void;
  currentView?: ViewMode;
  className?: string;
  filter?: FilterConfig;
  onFilterChange?: (filter: FilterConfig) => void;
  onCreateBoard?: () => void;
}

export const Header = memo(function Header({
  ticketCount = 0,
  lastUpdated = 'just now',
  onAIClick,
  onStatsClick,
  onSettingsClick,
  onViewChange,
  currentView = 'board',
  className,
  filter,
  onFilterChange,
  onCreateBoard,
}: HeaderProps) {
  const [activeView, setActiveView] = useState<ViewMode>(currentView);

  const handleViewChange = (view: ViewMode) => {
    setActiveView(view);
    onViewChange?.(view);
  };

  const views: Array<{ id: ViewMode; icon: typeof LayoutGrid; label: string }> = [
    { id: 'board', icon: LayoutGrid, label: 'Board' },
    { id: 'list', icon: List, label: 'List' },
    { id: 'timeline', icon: GanttChart, label: 'Timeline' },
    { id: 'calendar', icon: Calendar, label: 'Calendar' },
  ];

  return (
    <header
      className={cn(
        // Layout
        'flex items-center justify-between',
        'h-[52px] px-6',
        // Styling
        'bg-bg-secondary border-b border-border-subtle',
        // Positioning
        'sticky top-0 z-50',
        className
      )}
    >
      {/* Left: Board Switcher + Info */}
      <div className="flex items-center gap-3 min-w-0 flex-shrink">
        <BoardSwitcher onCreateBoard={onCreateBoard} />
        <span className="text-xs text-text-tertiary whitespace-nowrap">
          {ticketCount} ticket{ticketCount !== 1 ? 's' : ''} · Updated {lastUpdated}
        </span>
      </div>

      {/* Center: Search & Filter Bar */}
      <div className="flex-1 max-w-xl mx-8">
        <SearchFilterBar
          filter={filter || {}}
          onFilterChange={onFilterChange || (() => {})}
        />
      </div>

      {/* Right: Actions */}
      <div className="flex items-center gap-2 flex-shrink-0">
        {/* View Toggle */}
        <div
          className={cn(
            'flex items-center gap-0.5 p-0.5 rounded-lg',
            'bg-bg-elevated border border-border-subtle'
          )}
        >
          {views.map(({ id, icon: Icon, label }) => (
            <button
              key={id}
              onClick={() => handleViewChange(id)}
              className={cn(
                // Layout
                'flex items-center gap-1.5 px-2.5 h-7 rounded-md',
                // Typography
                'text-xs font-medium',
                // Transitions
                'transition-all duration-200',
                // Active state
                activeView === id
                  ? 'bg-bg-active text-text-primary shadow-sm'
                  : 'text-text-tertiary hover:text-text-secondary hover:bg-bg-hover'
              )}
              aria-label={label}
              aria-pressed={activeView === id}
            >
              <Icon className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">{label}</span>
            </button>
          ))}
        </div>

        {/* Theme Toggle */}
        <ThemeToggle />

        {/* Stats Button */}
        <button
          onClick={onStatsClick}
          className={cn(
            // Layout
            'flex items-center justify-center w-8 h-8 rounded-lg',
            // Styling
            'bg-bg-elevated border border-border-subtle',
            'text-text-tertiary',
            // Interaction
            'transition-all duration-200',
            'hover:bg-bg-hover hover:text-indigo-400 hover:border-indigo-500/50',
            'active:bg-bg-active',
            // Focus
            'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/50 focus-visible:border-accent'
          )}
          aria-label="Agent Stats"
          title="Agent Stats"
        >
          <BarChart3 className="w-4 h-4" />
        </button>

        {/* AI Button */}
        <button
          onClick={onAIClick}
          className={cn(
            // Layout
            'relative flex items-center gap-2 px-3 h-8 rounded-lg',
            // Background gradient
            'bg-gradient-to-br from-purple-600 to-indigo-600',
            // Typography
            'text-xs font-semibold text-white',
            // Effects
            'shadow-lg shadow-purple-500/20',
            // Transitions
            'transition-all duration-300',
            // Hover state
            'hover:shadow-xl hover:shadow-purple-500/40',
            'hover:scale-105',
            // Active state
            'active:scale-100',
            // Focus
            'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-purple-500/50',
            // Overflow for glow
            'overflow-hidden'
          )}
          aria-label="Open AI Assistant"
        >
          {/* Glow effect on hover */}
          <div
            className={cn(
              'absolute inset-0 opacity-0',
              'bg-gradient-to-br from-purple-400 to-indigo-400',
              'transition-opacity duration-300',
              'group-hover:opacity-20'
            )}
            aria-hidden="true"
          />

          {/* Content */}
          <Sparkles className="w-4 h-4 relative z-10" />
          <span className="relative z-10">AI</span>
        </button>

        {/* Settings Button */}
        <button
          onClick={onSettingsClick}
          className={cn(
            // Layout
            'flex items-center justify-center w-8 h-8 rounded-lg',
            // Styling
            'bg-bg-elevated border border-border-subtle',
            'text-text-tertiary',
            // Interaction
            'transition-all duration-200',
            'hover:bg-bg-hover hover:text-text-secondary hover:border-border-DEFAULT',
            'active:bg-bg-active',
            // Focus
            'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/50 focus-visible:border-accent'
          )}
          aria-label="Settings"
        >
          <Settings className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
});
