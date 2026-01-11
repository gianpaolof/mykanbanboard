// components/kanban/SearchFilterBar.tsx - Search and filter bar for tickets
import { useState, useCallback, useMemo, memo } from 'react';
import { Search, Filter, X, ChevronDown } from 'lucide-react';
import { AnimatePresence, motion } from 'framer-motion';
import { cn } from '@/lib/utils';
import { useBoardStore } from '@/stores/boardStore';
import type { Priority, FilterConfig } from '@/types';

// ===========================================
// CONSTANTS
// ===========================================

const PRIORITY_OPTIONS: { value: Priority; label: string; emoji: string }[] = [
  { value: 'critical', label: 'Critical', emoji: '🔴' },
  { value: 'high', label: 'High', emoji: '🟠' },
  { value: 'medium', label: 'Medium', emoji: '🟡' },
  { value: 'low', label: 'Low', emoji: '🟢' },
];

// ===========================================
// COMPONENT
// ===========================================

interface SearchFilterBarProps {
  filter: FilterConfig;
  onFilterChange: (filter: FilterConfig) => void;
}

export const SearchFilterBar = memo(function SearchFilterBar({
  filter,
  onFilterChange,
}: SearchFilterBarProps) {
  const labels = useBoardStore((state) => state.labels);

  const [isFilterOpen, setIsFilterOpen] = useState(false);

  // Count active filters
  const activeFilterCount = useMemo(() => {
    let count = 0;
    if (filter.priority && filter.priority.length > 0) count++;
    if (filter.labels && filter.labels.length > 0) count++;
    if (filter.dueBefore || filter.dueAfter) count++;
    return count;
  }, [filter]);

  // Handle search change
  const handleSearchChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      onFilterChange({ ...filter, search: e.target.value || undefined });
    },
    [filter, onFilterChange]
  );

  // Clear search
  const handleClearSearch = useCallback(() => {
    onFilterChange({ ...filter, search: undefined });
  }, [filter, onFilterChange]);

  // Toggle priority filter
  const handleTogglePriority = useCallback(
    (priority: Priority) => {
      const current = filter.priority || [];
      const newPriorities = current.includes(priority)
        ? current.filter((p) => p !== priority)
        : [...current, priority];
      onFilterChange({
        ...filter,
        priority: newPriorities.length > 0 ? newPriorities : undefined,
      });
    },
    [filter, onFilterChange]
  );

  // Toggle label filter
  const handleToggleLabel = useCallback(
    (labelId: string) => {
      const current = filter.labels || [];
      const newLabels = current.includes(labelId)
        ? current.filter((l) => l !== labelId)
        : [...current, labelId];
      onFilterChange({
        ...filter,
        labels: newLabels.length > 0 ? newLabels : undefined,
      });
    },
    [filter, onFilterChange]
  );

  // Clear all filters
  const handleClearFilters = useCallback(() => {
    onFilterChange({});
    setIsFilterOpen(false);
  }, [onFilterChange]);

  // Check if has any filters
  const hasFilters = filter.search || activeFilterCount > 0;

  return (
    <div className="flex items-center gap-2">
      {/* Search Input */}
      <div className="relative flex-1 max-w-xs">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted pointer-events-none" />
        <input
          type="text"
          value={filter.search || ''}
          onChange={handleSearchChange}
          placeholder="Search tickets..."
          className={cn(
            'w-full pl-9 pr-8 py-2',
            'bg-bg-tertiary border border-border-subtle rounded-lg',
            'text-sm text-text-primary placeholder:text-text-muted',
            'focus:outline-none focus:border-accent focus:ring-2 focus:ring-accent/20',
            'transition-colors'
          )}
        />
        {filter.search && (
          <button
            onClick={handleClearSearch}
            className="absolute right-2 top-1/2 -translate-y-1/2 p-1 rounded text-text-muted hover:text-text-secondary transition-colors"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        )}
      </div>

      {/* Filter Button */}
      <div className="relative">
        <button
          onClick={() => setIsFilterOpen(!isFilterOpen)}
          className={cn(
            'flex items-center gap-2 px-3 py-2 rounded-lg',
            'text-sm font-medium transition-colors',
            isFilterOpen || activeFilterCount > 0
              ? 'bg-accent text-white'
              : 'bg-bg-tertiary text-text-secondary hover:bg-bg-hover'
          )}
        >
          <Filter className="w-4 h-4" />
          <span>Filter</span>
          {activeFilterCount > 0 && (
            <span className="ml-1 px-1.5 py-0.5 rounded-full bg-white/20 text-2xs">
              {activeFilterCount}
            </span>
          )}
          <ChevronDown
            className={cn(
              'w-3.5 h-3.5 transition-transform',
              isFilterOpen && 'rotate-180'
            )}
          />
        </button>

        {/* Filter Dropdown */}
        <AnimatePresence>
          {isFilterOpen && (
            <motion.div
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.15 }}
              className={cn(
                'absolute right-0 top-full mt-2 z-50',
                'w-72 p-4',
                'bg-bg-elevated border border-border-subtle rounded-xl shadow-xl'
              )}
            >
              {/* Priority Filter */}
              <div className="mb-4">
                <h4 className="text-xs font-semibold uppercase tracking-wide text-text-muted mb-2">
                  Priority
                </h4>
                <div className="flex flex-wrap gap-1.5">
                  {PRIORITY_OPTIONS.map((opt) => {
                    const isSelected = filter.priority?.includes(opt.value);
                    return (
                      <button
                        key={opt.value}
                        onClick={() => handleTogglePriority(opt.value)}
                        className={cn(
                          'px-2.5 py-1 rounded-lg text-xs font-medium transition-colors',
                          isSelected
                            ? 'bg-accent text-white'
                            : 'bg-bg-tertiary text-text-secondary hover:bg-bg-hover'
                        )}
                      >
                        {opt.emoji} {opt.label}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Labels Filter */}
              {labels.length > 0 && (
                <div className="mb-4">
                  <h4 className="text-xs font-semibold uppercase tracking-wide text-text-muted mb-2">
                    Labels
                  </h4>
                  <div className="flex flex-wrap gap-1.5">
                    {labels.map((label) => {
                      const isSelected = filter.labels?.includes(label.id);
                      return (
                        <button
                          key={label.id}
                          onClick={() => handleToggleLabel(label.id)}
                          className={cn(
                            'px-2.5 py-1 rounded-full text-xs font-medium transition-all',
                            'flex items-center gap-1.5',
                            isSelected
                              ? 'ring-2 ring-offset-1 ring-offset-bg-elevated'
                              : 'opacity-70 hover:opacity-100'
                          )}
                          style={{
                            backgroundColor: `${label.color}20`,
                            color: label.color,
                            ...(isSelected && { ringColor: label.color }),
                          }}
                        >
                          <span
                            className="w-2 h-2 rounded-full"
                            style={{ backgroundColor: label.color }}
                          />
                          {label.name}
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Clear Filters */}
              {hasFilters && (
                <button
                  onClick={handleClearFilters}
                  className={cn(
                    'w-full px-3 py-2 rounded-lg',
                    'text-sm font-medium text-status-error',
                    'hover:bg-status-error/10 transition-colors'
                  )}
                >
                  Clear all filters
                </button>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
});
