// components/kanban/TicketModal.tsx
import { useState, useCallback, useMemo, memo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Sparkles, GitBranch, Trash2, Check, Loader2, XCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import { api } from '@/lib/tauri';
import { useBoardStore } from '@/stores/boardStore';
import type { Ticket, Effort, Priority } from '@/types';
import type { AgentTriageResult } from '@/lib/tauri';

interface SubtaskSuggestion {
  title: string;
  description: string;
  effort?: string;
  selected: boolean;
}

const PRIORITY_CONFIG = {
  critical: { emoji: '🔴', label: 'Critical', color: 'text-red-400' },
  high: { emoji: '🟠', label: 'High', color: 'text-orange-400' },
  medium: { emoji: '🟡', label: 'Medium', color: 'text-yellow-400' },
  low: { emoji: '🟢', label: 'Low', color: 'text-gray-400' },
} as const;

// Effort badge colors - moved outside component
const EFFORT_COLORS: Record<string, string> = {
  xs: 'bg-green-500/15 text-green-300 border-green-500/30',
  s: 'bg-blue-500/15 text-blue-300 border-blue-500/30',
  m: 'bg-yellow-500/15 text-yellow-300 border-yellow-500/30',
  l: 'bg-orange-500/15 text-orange-300 border-orange-500/30',
  xl: 'bg-red-500/15 text-red-300 border-red-500/30',
};

const getEffortColor = (effort?: string) =>
  EFFORT_COLORS[effort || ''] || 'bg-zinc-500/15 text-zinc-300 border-zinc-500/30';

interface TicketModalProps {
  ticket: Ticket;
  onClose: () => void;
  onSave?: (updates: Partial<Ticket>) => void;
  onDelete?: () => void;
}

export const TicketModal = memo(function TicketModal({
  ticket,
  onClose,
  onSave,
  onDelete,
}: TicketModalProps) {
  const { addTicket } = useBoardStore();

  // Form state
  const [description, setDescription] = useState(ticket.description || '');
  const [priority, setPriority] = useState<Priority | undefined>(ticket.priority);
  const [effort, setEffort] = useState<Effort | undefined>(ticket.effort);

  // AI Triage state
  const [isTriaging, setIsTriaging] = useState(false);
  const [triageResult, setTriageResult] = useState<AgentTriageResult | null>(null);
  const [triageError, setTriageError] = useState<string | null>(null);

  // Decompose state
  const [isDecomposing, setIsDecomposing] = useState(false);
  const [decomposeResult, setDecomposeResult] = useState<SubtaskSuggestion[] | null>(null);
  const [isCreatingSubtasks, setIsCreatingSubtasks] = useState(false);

  // Handle AI Triage
  const handleAITriage = useCallback(async () => {
    setIsTriaging(true);
    setTriageError(null);
    setTriageResult(null);

    try {
      const result = await api.agent.triage(
        ticket.id,
        ticket.title,
        description || ticket.description || ''
      );
      setTriageResult(result);
    } catch (error) {
      console.error('Triage failed:', error);
      setTriageError(error instanceof Error ? error.message : 'Failed to analyze ticket');
    } finally {
      setIsTriaging(false);
    }
  }, [ticket.id, ticket.title, ticket.description, description]);

  // Apply AI suggestions to form
  const applyTriageSuggestions = useCallback(() => {
    if (!triageResult) return;

    if (triageResult.priority) {
      setPriority(triageResult.priority as Priority);
    }
    if (triageResult.effort) {
      setEffort(triageResult.effort as Effort);
    }
    // Note: labels would need to be mapped from names to IDs
    // For now we skip label application

    // Clear the result after applying
    setTriageResult(null);
  }, [triageResult]);

  // Dismiss triage results
  const dismissTriageResult = useCallback(() => {
    setTriageResult(null);
    setTriageError(null);
  }, []);

  const handleDecompose = useCallback(async () => {
    setIsDecomposing(true);
    setDecomposeResult(null);

    try {
      const result = await api.agent.decompose(
        ticket.id,
        ticket.title,
        ticket.description || ''
      );

      // Convert to subtask suggestions with selection state
      const suggestions: SubtaskSuggestion[] = result.subtasks.map((subtask) => ({
        ...subtask,
        selected: true, // All selected by default
      }));

      setDecomposeResult(suggestions);
    } catch (error) {
      console.error('Decompose failed:', error);
      // TODO: Show error toast
    } finally {
      setIsDecomposing(false);
    }
  }, [ticket.id, ticket.title, ticket.description]);

  const toggleSubtaskSelection = useCallback((index: number) => {
    setDecomposeResult((prev) => {
      if (!prev) return prev;
      return prev.map((subtask, i) =>
        i === index ? { ...subtask, selected: !subtask.selected } : subtask
      );
    });
  }, []);

  const createSubtasks = useCallback(async () => {
    if (!decomposeResult) return;

    const selectedSubtasks = decomposeResult.filter(s => s.selected);
    if (selectedSubtasks.length === 0) return;

    setIsCreatingSubtasks(true);

    try {
      for (const subtask of selectedSubtasks) {
        await addTicket({
          title: subtask.title,
          description: subtask.description,
          effort: subtask.effort as Effort | undefined,
          columnId: ticket.columnId,
        });
      }

      // Close modal after creating subtasks
      onClose();
    } catch (error) {
      console.error('Failed to create subtasks:', error);
      // TODO: Show error toast
    } finally {
      setIsCreatingSubtasks(false);
    }
  }, [decomposeResult, addTicket, ticket.columnId, onClose]);

  const cancelDecompose = useCallback(() => {
    setDecomposeResult(null);
  }, []);

  // Memoize selected subtask count
  const selectedSubtaskCount = useMemo(
    () => decomposeResult?.filter(s => s.selected).length ?? 0,
    [decomposeResult]
  );

  // Memoize handler for description change
  const handleDescriptionChange = useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => setDescription(e.target.value),
    []
  );

  // Memoize handler for priority change
  const handlePriorityChange = useCallback(
    (e: React.ChangeEvent<HTMLSelectElement>) => setPriority(e.target.value as Priority),
    []
  );

  // Memoize handler for effort change
  const handleEffortChange = useCallback(
    (e: React.ChangeEvent<HTMLSelectElement>) => setEffort(e.target.value as Effort),
    []
  );

  // Memoize save handler
  const handleSave = useCallback(() => {
    onSave?.({ description, priority, effort });
  }, [onSave, description, priority, effort]);

  return (
    <AnimatePresence>
      {/* Overlay */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
        className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center"
      >
        {/* Modal */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
          transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
          onClick={(e) => e.stopPropagation()}
          className={cn(
            'w-[640px] max-h-[85vh]',
            'bg-zinc-900 border border-zinc-800',
            'rounded-2xl shadow-2xl',
            'flex flex-col'
          )}
        >
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-zinc-800">
            <h2 className="font-bold text-lg">{ticket.title}</h2>
            <button
              onClick={onClose}
              className="w-8 h-8 rounded-lg flex items-center justify-center text-zinc-500 hover:text-zinc-100 hover:bg-zinc-800 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Body */}
          <div className="flex-1 overflow-y-auto p-4 space-y-6">
            {/* Description */}
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wide text-zinc-500 mb-2">
                Description
              </label>
              <textarea
                value={description}
                onChange={handleDescriptionChange}
                placeholder="Add a description..."
                className={cn(
                  'w-full min-h-[120px] p-3',
                  'bg-zinc-950 border border-zinc-800 rounded-lg',
                  'text-zinc-100 text-sm leading-relaxed',
                  'focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20',
                  'resize-y transition-colors'
                )}
              />
            </div>

            {/* AI Triage Result Panel */}
            <AnimatePresence>
              {(triageResult || triageError) && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="overflow-hidden"
                >
                  <div
                    className={cn(
                      'p-4 rounded-lg border',
                      'bg-gradient-to-br from-zinc-900/50 to-zinc-950/50 backdrop-blur-sm',
                      triageError
                        ? 'border-red-500/30'
                        : 'border-indigo-500/30'
                    )}
                  >
                    {triageError ? (
                      // Error state
                      <div className="space-y-2">
                        <div className="flex items-center gap-2 text-red-400">
                          <XCircle className="w-4 h-4" />
                          <span className="font-semibold text-sm">Triage Failed</span>
                        </div>
                        <p className="text-sm text-zinc-400">{triageError}</p>
                        <button
                          onClick={dismissTriageResult}
                          className="text-xs text-zinc-500 hover:text-zinc-300"
                        >
                          Dismiss
                        </button>
                      </div>
                    ) : (
                      // Success state with suggestions
                      <div className="space-y-3">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2 text-indigo-400">
                            <Sparkles className="w-4 h-4" />
                            <span className="font-semibold text-sm">AI Suggestions</span>
                          </div>
                          <button
                            onClick={dismissTriageResult}
                            className="text-zinc-500 hover:text-zinc-300"
                          >
                            <X className="w-4 h-4" />
                          </button>
                        </div>

                        {/* Suggested values */}
                        <div className="grid grid-cols-3 gap-3">
                          {triageResult?.priority && (
                            <div className="space-y-1">
                              <div className="text-xs text-zinc-500 uppercase tracking-wide">
                                Priority
                              </div>
                              <div
                                className={cn(
                                  'text-sm font-medium',
                                  PRIORITY_CONFIG[triageResult.priority as Priority]?.color
                                )}
                              >
                                {PRIORITY_CONFIG[triageResult.priority as Priority]?.emoji}{' '}
                                {PRIORITY_CONFIG[triageResult.priority as Priority]?.label}
                              </div>
                            </div>
                          )}

                          {triageResult?.effort && (
                            <div className="space-y-1">
                              <div className="text-xs text-zinc-500 uppercase tracking-wide">
                                Effort
                              </div>
                              <div className="text-sm font-medium text-zinc-300">
                                {triageResult.effort.toUpperCase()}
                              </div>
                            </div>
                          )}

                          {triageResult?.labels && triageResult.labels.length > 0 && (
                            <div className="space-y-1">
                              <div className="text-xs text-zinc-500 uppercase tracking-wide">
                                Labels
                              </div>
                              <div className="flex gap-1 flex-wrap">
                                {triageResult.labels.map((label, idx) => (
                                  <span
                                    key={idx}
                                    className="px-2 py-0.5 text-xs rounded bg-purple-500/20 text-purple-300"
                                  >
                                    {label}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>

                        {/* Reasoning */}
                        {triageResult?.reasoning && (
                          <div className="pt-2 border-t border-zinc-800">
                            <div className="text-xs text-zinc-500 uppercase tracking-wide mb-1">
                              Reasoning
                            </div>
                            <p className="text-sm text-zinc-400 leading-relaxed">
                              {triageResult.reasoning}
                            </p>
                          </div>
                        )}

                        {/* Action buttons */}
                        <div className="flex gap-2 pt-2">
                          <button
                            onClick={applyTriageSuggestions}
                            className={cn(
                              'flex-1 px-3 py-2 rounded-lg text-sm font-medium',
                              'bg-indigo-500 text-white',
                              'hover:bg-indigo-400',
                              'flex items-center justify-center gap-2',
                              'transition-colors'
                            )}
                          >
                            <Check className="w-4 h-4" />
                            Apply Suggestions
                          </button>
                          <button
                            onClick={dismissTriageResult}
                            className={cn(
                              'px-3 py-2 rounded-lg text-sm font-medium',
                              'bg-zinc-800 text-zinc-300',
                              'hover:bg-zinc-700',
                              'transition-colors'
                            )}
                          >
                            Dismiss
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Fields Grid */}
            <div className="grid grid-cols-2 gap-4">
              {/* Priority */}
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wide text-zinc-500 mb-2">
                  Priority
                </label>
                <select
                  value={priority || 'medium'}
                  onChange={handlePriorityChange}
                  className={cn(
                    'w-full p-2',
                    'bg-zinc-950 border border-zinc-800 rounded-lg',
                    'text-zinc-100 text-sm',
                    'focus:outline-none focus:border-indigo-500'
                  )}
                >
                  <option value="low">🟢 Low</option>
                  <option value="medium">🟡 Medium</option>
                  <option value="high">🟠 High</option>
                  <option value="critical">🔴 Critical</option>
                </select>
              </div>

              {/* Effort */}
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wide text-zinc-500 mb-2">
                  Effort
                </label>
                <select
                  value={effort || 'm'}
                  onChange={handleEffortChange}
                  className={cn(
                    'w-full p-2',
                    'bg-zinc-950 border border-zinc-800 rounded-lg',
                    'text-zinc-100 text-sm',
                    'focus:outline-none focus:border-indigo-500'
                  )}
                >
                  <option value="xs">XS - &lt; 1 hour</option>
                  <option value="s">S - Half day</option>
                  <option value="m">M - 1-2 days</option>
                  <option value="l">L - 3-5 days</option>
                  <option value="xl">XL - 1+ week</option>
                </select>
              </div>
            </div>

            {/* Labels */}
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wide text-zinc-500 mb-2">
                Labels
              </label>
              <div className="flex gap-2 flex-wrap">
                {ticket.labels.map((label) => (
                  <span
                    key={label.id}
                    className="px-2 py-1 text-xs font-semibold rounded bg-purple-500/15 text-purple-300"
                  >
                    {label.name}
                  </span>
                ))}
                <button className="px-2 py-1 text-xs text-zinc-500 hover:text-zinc-300">
                  + Add label
                </button>
              </div>
            </div>

            {/* Decompose Results */}
            {decomposeResult && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className={cn(
                  'p-4 rounded-xl border',
                  'bg-indigo-500/5 border-indigo-500/20'
                )}
              >
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-semibold text-indigo-300 flex items-center gap-2">
                    <GitBranch className="w-4 h-4" />
                    Suggested Subtasks ({selectedSubtaskCount} selected)
                  </h3>
                </div>

                <div className="space-y-2 mb-4">
                  {decomposeResult.map((subtask, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.05 }}
                      onClick={() => toggleSubtaskSelection(index)}
                      className={cn(
                        'p-3 rounded-lg border cursor-pointer transition-all',
                        'hover:border-indigo-500/40',
                        subtask.selected
                          ? 'bg-zinc-800/50 border-indigo-500/30'
                          : 'bg-zinc-900/50 border-zinc-800 opacity-50'
                      )}
                    >
                      <div className="flex items-start gap-3">
                        {/* Checkbox */}
                        <div
                          className={cn(
                            'w-5 h-5 rounded flex-shrink-0 flex items-center justify-center transition-all',
                            'border-2 mt-0.5',
                            subtask.selected
                              ? 'bg-indigo-500 border-indigo-500'
                              : 'border-zinc-600'
                          )}
                        >
                          {subtask.selected && <Check className="w-3 h-3 text-white" />}
                        </div>

                        {/* Content */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <h4 className="text-sm font-medium text-zinc-100">
                              {subtask.title}
                            </h4>
                            {subtask.effort && (
                              <span
                                className={cn(
                                  'px-2 py-0.5 text-xs font-semibold rounded border uppercase',
                                  getEffortColor(subtask.effort)
                                )}
                              >
                                {subtask.effort}
                              </span>
                            )}
                          </div>
                          <p className="text-xs text-zinc-400 line-clamp-2">
                            {subtask.description}
                          </p>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>

                {/* Actions */}
                <div className="flex gap-2">
                  <button
                    onClick={createSubtasks}
                    disabled={isCreatingSubtasks || selectedSubtaskCount === 0}
                    className={cn(
                      'flex-1 px-4 py-2 rounded-lg text-sm font-medium',
                      'bg-indigo-500 text-white',
                      'hover:bg-indigo-400 transition-colors',
                      'disabled:opacity-50 disabled:cursor-not-allowed',
                      'flex items-center justify-center gap-2'
                    )}
                  >
                    {isCreatingSubtasks ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Creating...
                      </>
                    ) : (
                      <>Create Selected ({selectedSubtaskCount})</>
                    )}
                  </button>
                  <button
                    onClick={cancelDecompose}
                    disabled={isCreatingSubtasks}
                    className={cn(
                      'px-4 py-2 rounded-lg text-sm font-medium',
                      'bg-zinc-800 text-zinc-300 border border-zinc-700',
                      'hover:bg-zinc-700 transition-colors',
                      'disabled:opacity-50 disabled:cursor-not-allowed'
                    )}
                  >
                    Cancel
                  </button>
                </div>
              </motion.div>
            )}
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between p-4 border-t border-zinc-800">
            <div className="flex gap-2">
              {/* AI Triage Button */}
              <button
                onClick={handleAITriage}
                disabled={isTriaging}
                className={cn(
                  'px-3 py-2 rounded-lg text-sm font-medium',
                  'bg-gradient-to-r from-indigo-500 to-purple-500 text-white',
                  'hover:shadow-lg hover:shadow-indigo-500/25',
                  'flex items-center gap-2 transition-all',
                  'disabled:opacity-50 disabled:cursor-not-allowed'
                )}
              >
                {isTriaging ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4" />
                    AI Triage
                  </>
                )}
              </button>

              {/* Decompose Button */}
              <button
                onClick={handleDecompose}
                disabled={isDecomposing || !!decomposeResult}
                className={cn(
                  'px-3 py-2 rounded-lg text-sm font-medium',
                  'bg-zinc-800 text-zinc-100 border border-zinc-700',
                  'hover:bg-zinc-700',
                  'flex items-center gap-2 transition-colors',
                  'disabled:opacity-50 disabled:cursor-not-allowed'
                )}
              >
                {isDecomposing ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <GitBranch className="w-4 h-4" />
                    Decompose
                  </>
                )}
              </button>
            </div>

            <div className="flex gap-2">
              <button
                onClick={onDelete}
                className="px-3 py-2 rounded-lg text-sm font-medium text-red-400 hover:bg-red-500/10 flex items-center gap-2 transition-colors"
              >
                <Trash2 className="w-4 h-4" />
                Delete
              </button>
              <button
                onClick={handleSave}
                className="px-4 py-2 rounded-lg text-sm font-medium bg-indigo-500 text-white hover:bg-indigo-400 transition-colors"
              >
                Save changes
              </button>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
});
