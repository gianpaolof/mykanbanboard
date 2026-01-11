// components/layout/Header.tsx
import { useState } from 'react';
import {
  Search,
  LayoutGrid,
  List,
  GanttChart,
  Sparkles,
  Settings,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { ThemeToggle } from '@/components/ui/ThemeToggle';

type ViewMode = 'board' | 'list' | 'timeline';

interface HeaderProps {
  boardTitle?: string;
  ticketCount?: number;
  lastUpdated?: string;
  onSearchClick?: () => void;
  onAIClick?: () => void;
  onSettingsClick?: () => void;
  onViewChange?: (view: ViewMode) => void;
  currentView?: ViewMode;
  className?: string;
}

export function Header({
  boardTitle = 'My Project',
  ticketCount = 24,
  lastUpdated = '2m ago',
  onSearchClick,
  onAIClick,
  onSettingsClick,
  onViewChange,
  currentView = 'board',
  className,
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
      {/* Left: Board Info */}
      <div className="flex items-center gap-3 min-w-0 flex-shrink">
        <h1 className="text-base font-semibold text-text-primary truncate">
          {boardTitle}
        </h1>
        <span className="text-xs text-text-tertiary whitespace-nowrap">
          {ticketCount} tickets · Updated {lastUpdated}
        </span>
      </div>

      {/* Center: Search Bar */}
      <div className="flex-1 max-w-md mx-8">
        <button
          onClick={onSearchClick}
          className={cn(
            // Layout
            'w-full flex items-center gap-3 px-3 h-8',
            // Styling
            'bg-bg-elevated rounded-lg',
            'border border-border-subtle',
            // Text
            'text-sm text-text-tertiary',
            // Interaction
            'transition-all duration-200',
            'hover:border-border-DEFAULT hover:bg-bg-hover',
            'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/50 focus-visible:border-accent'
          )}
        >
          <Search className="w-4 h-4 flex-shrink-0" />
          <span className="flex-1 text-left">Search tickets...</span>
          <kbd
            className={cn(
              'px-1.5 py-0.5 rounded',
              'bg-bg-tertiary border border-border-subtle',
              'text-2xs font-mono text-text-tertiary',
              'flex items-center gap-0.5'
            )}
          >
            ⌘K
          </kbd>
        </button>
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
}
