// components/ai/SuggestionsWidget.tsx
import { useState, useEffect, useCallback, memo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Lightbulb,
  Clock,
  AlertTriangle,
  Tag,
  Copy,
  Layers,
  X,
  RefreshCw,
  Loader2,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { cn } from '../../lib/utils';

// ===========================================
// TYPES
// ===========================================

interface Suggestion {
  type: string;
  message: string;
  action: string;
  priority: 'low' | 'medium' | 'high';
  ticket_id?: string;
  column_id?: string;
}

interface Column {
  id: string;
  name: string;
  position?: number;
}

interface Ticket {
  id: string;
  title: string;
  column_id: string;
  priority?: string;
  effort?: string;
  labels?: string[];
}

interface SuggestionsWidgetProps {
  columns: Column[];
  tickets: Ticket[];
  className?: string;
  onDismiss?: (index: number) => void;
}

// ===========================================
// CONSTANTS
// ===========================================

const AGENT_API_BASE = 'http://localhost:8765/api';

const SUGGESTION_ICONS: Record<string, typeof Clock> = {
  stale_ticket: Clock,
  overloaded_column: Layers,
  missing_labels: Tag,
  similar_tickets: Copy,
  priority_imbalance: AlertTriangle,
  blocked_ticket: AlertTriangle,
  effort_mismatch: AlertTriangle,
};

const PRIORITY_COLORS: Record<string, string> = {
  high: 'bg-red-500/20 text-red-400 border-red-500/30',
  medium: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  low: 'bg-zinc-500/20 text-zinc-400 border-zinc-500/30',
};

// ===========================================
// SUGGESTION ITEM COMPONENT
// ===========================================

interface SuggestionItemProps {
  suggestion: Suggestion;
  onDismiss: () => void;
}

const SuggestionItem = memo(function SuggestionItem({
  suggestion,
  onDismiss,
}: SuggestionItemProps) {
  const Icon = SUGGESTION_ICONS[suggestion.type] || Lightbulb;
  const priorityColor = PRIORITY_COLORS[suggestion.priority] || PRIORITY_COLORS.medium;

  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 10, height: 0 }}
      className={cn(
        'p-3 rounded-lg border bg-zinc-900/50',
        'hover:bg-zinc-800/50 transition-colors',
        'border-zinc-800'
      )}
    >
      <div className="flex items-start gap-3">
        <div className={cn('p-1.5 rounded-lg', priorityColor)}>
          <Icon className="w-4 h-4" />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span
              className={cn(
                'px-1.5 py-0.5 text-2xs font-semibold rounded uppercase',
                priorityColor
              )}
            >
              {suggestion.priority}
            </span>
          </div>
          <p className="text-sm text-zinc-300 leading-relaxed">
            {suggestion.message}
          </p>
          {suggestion.action && (
            <p className="text-xs text-zinc-500 mt-1">{suggestion.action}</p>
          )}
        </div>

        <button
          onClick={onDismiss}
          className="p-1 rounded hover:bg-zinc-700 text-zinc-500 hover:text-zinc-300 transition-colors flex-shrink-0"
          title="Dismiss"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      </div>
    </motion.div>
  );
});

// ===========================================
// SUGGESTIONS WIDGET
// ===========================================

export const SuggestionsWidget = memo(function SuggestionsWidget({
  columns,
  tickets,
  className,
  onDismiss,
}: SuggestionsWidgetProps) {
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [dismissedIndexes, setDismissedIndexes] = useState<Set<number>>(new Set());
  const [isLoading, setIsLoading] = useState(false);
  const [isExpanded, setIsExpanded] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSuggestions = useCallback(async () => {
    if (columns.length === 0 && tickets.length === 0) {
      setSuggestions([]);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${AGENT_API_BASE}/agent/suggestions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          columns: columns.map((c) => ({
            id: c.id,
            name: c.name,
            position: c.position || 0,
          })),
          tickets: tickets.map((t) => ({
            id: t.id,
            title: t.title,
            column_id: t.column_id,
            priority: t.priority || 'medium',
            effort: t.effort || 'm',
            labels: t.labels || [],
          })),
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch suggestions: ${response.status}`);
      }

      const data = await response.json();
      setSuggestions(data.suggestions || []);
      setDismissedIndexes(new Set());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load suggestions');
    } finally {
      setIsLoading(false);
    }
  }, [columns, tickets]);

  // Fetch suggestions when columns/tickets change
  useEffect(() => {
    fetchSuggestions();
  }, [fetchSuggestions]);

  const handleDismiss = useCallback(
    (index: number) => {
      setDismissedIndexes((prev) => new Set([...prev, index]));
      onDismiss?.(index);
    },
    [onDismiss]
  );

  const visibleSuggestions = suggestions.filter(
    (_, index) => !dismissedIndexes.has(index)
  );

  const highPriorityCount = visibleSuggestions.filter(
    (s) => s.priority === 'high'
  ).length;

  if (error) {
    return (
      <div className={cn('p-4 rounded-xl bg-zinc-900 border border-zinc-800', className)}>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Lightbulb className="w-5 h-5 text-yellow-400" />
            <h3 className="font-semibold text-white">Suggestions</h3>
          </div>
          <button
            onClick={fetchSuggestions}
            className="p-1.5 rounded-lg hover:bg-zinc-800 text-zinc-500 hover:text-zinc-300 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
        <p className="text-sm text-zinc-500 text-center py-4">{error}</p>
      </div>
    );
  }

  return (
    <div className={cn('rounded-xl bg-zinc-900 border border-zinc-800', className)}>
      {/* Header */}
      <button
        onClick={() => setIsExpanded((prev) => !prev)}
        className="w-full flex items-center justify-between p-4 hover:bg-zinc-800/30 transition-colors rounded-t-xl"
      >
        <div className="flex items-center gap-2">
          <Lightbulb className="w-5 h-5 text-yellow-400" />
          <h3 className="font-semibold text-white">Suggestions</h3>
          {visibleSuggestions.length > 0 && (
            <span
              className={cn(
                'px-1.5 py-0.5 text-2xs font-semibold rounded-full',
                highPriorityCount > 0
                  ? 'bg-red-500/20 text-red-400'
                  : 'bg-zinc-700 text-zinc-400'
              )}
            >
              {visibleSuggestions.length}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={(e) => {
              e.stopPropagation();
              fetchSuggestions();
            }}
            disabled={isLoading}
            className="p-1.5 rounded-lg hover:bg-zinc-700 text-zinc-500 hover:text-zinc-300 transition-colors disabled:opacity-50"
            title="Refresh"
          >
            <RefreshCw className={cn('w-4 h-4', isLoading && 'animate-spin')} />
          </button>
          {isExpanded ? (
            <ChevronUp className="w-4 h-4 text-zinc-500" />
          ) : (
            <ChevronDown className="w-4 h-4 text-zinc-500" />
          )}
        </div>
      </button>

      {/* Content */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0 }}
            animate={{ height: 'auto' }}
            exit={{ height: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="px-4 pb-4 space-y-2">
              {isLoading && suggestions.length === 0 ? (
                <div className="flex items-center justify-center py-6">
                  <Loader2 className="w-6 h-6 text-yellow-400 animate-spin" />
                </div>
              ) : visibleSuggestions.length === 0 ? (
                <p className="text-sm text-zinc-500 text-center py-4">
                  No suggestions right now. Your board looks great!
                </p>
              ) : (
                <AnimatePresence mode="popLayout">
                  {visibleSuggestions.map((suggestion, index) => (
                    <SuggestionItem
                      key={`${suggestion.type}-${index}`}
                      suggestion={suggestion}
                      onDismiss={() => handleDismiss(suggestions.indexOf(suggestion))}
                    />
                  ))}
                </AnimatePresence>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
});

export default SuggestionsWidget;
