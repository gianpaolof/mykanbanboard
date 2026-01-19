// components/kanban/CreateTicketModal.tsx - Modal for creating new tickets
import { useState, useCallback, useEffect, useRef, memo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Sparkles, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useBoardStore } from '@/stores/boardStore';
import { useProjectStore } from '@/stores/projectStore';
import { api } from '@/lib/tauri';
import type { Priority, Effort } from '@/types';
import type { AgentTriageResult } from '@/lib/tauri';

// ===========================================
// CONSTANTS
// ===========================================

const PRIORITY_OPTIONS: { value: Priority; label: string; emoji: string }[] = [
  { value: 'low', label: 'Low', emoji: '🟢' },
  { value: 'medium', label: 'Medium', emoji: '🟡' },
  { value: 'high', label: 'High', emoji: '🟠' },
  { value: 'critical', label: 'Critical', emoji: '🔴' },
];

const EFFORT_OPTIONS: { value: Effort; label: string }[] = [
  { value: 'xs', label: 'XS' },
  { value: 's', label: 'S' },
  { value: 'm', label: 'M' },
  { value: 'l', label: 'L' },
  { value: 'xl', label: 'XL' },
];

// ===========================================
// COMPONENT
// ===========================================

interface CreateTicketModalProps {
  isOpen: boolean;
  onClose: () => void;
  defaultColumnId?: string;
}

export const CreateTicketModal = memo(function CreateTicketModal({
  isOpen,
  onClose,
  defaultColumnId,
}: CreateTicketModalProps) {
  const columns = useBoardStore((state) => state.columns);
  const labels = useBoardStore((state) => state.labels);
  const tickets = useBoardStore((state) => state.tickets);
  const addTicket = useBoardStore((state) => state.addTicket);
  const currentBoardId = useBoardStore((state) => state.currentBoardId);
  const board = useBoardStore((state) => state.board);

  // Get project context for AI operations
  const getAgentProjectContext = useProjectStore((state) => state.getAgentProjectContext);
  const getAgentBoardContext = useProjectStore((state) => state.getAgentBoardContext);

  // Form state
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [columnId, setColumnId] = useState<string>('');
  const [priority, setPriority] = useState<Priority | undefined>(undefined);
  const [effort, setEffort] = useState<Effort | undefined>(undefined);
  const [selectedLabels, setSelectedLabels] = useState<string[]>([]);
  const [dueDate, setDueDate] = useState('');

  // AI Triage state
  const [isTriaging, setIsTriaging] = useState(false);
  const [triageResult, setTriageResult] = useState<AgentTriageResult | null>(null);

  // Submission state
  const [isSubmitting, setIsSubmitting] = useState(false);

  const titleInputRef = useRef<HTMLInputElement>(null);

  // Set default column when opening
  useEffect(() => {
    if (isOpen) {
      // Reset form
      setTitle('');
      setDescription('');
      setPriority(undefined);
      setEffort(undefined);
      setSelectedLabels([]);
      setDueDate('');
      setTriageResult(null);

      // Set default column
      if (defaultColumnId && columns.some((c) => c.id === defaultColumnId)) {
        setColumnId(defaultColumnId);
      } else if (columns.length > 0) {
        // Default to first column (usually Backlog)
        setColumnId(columns[0].id);
      }

      // Focus title input
      setTimeout(() => titleInputRef.current?.focus(), 100);
    }
  }, [isOpen, defaultColumnId, columns]);

  // Handle escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        e.preventDefault();
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  // AI Triage
  const handleAITriage = useCallback(async () => {
    if (!title.trim()) return;

    setIsTriaging(true);
    try {
      // Get contexts for AI
      const projectContext = getAgentProjectContext();
      const totalTickets = Object.values(tickets).flat().length;
      const boardContext = currentBoardId && board
        ? getAgentBoardContext(
            currentBoardId,
            board.name,
            columns.map((c) => ({ id: c.id, name: c.name })),
            labels.map((l) => l.name),
            totalTickets
          )
        : undefined;

      const result = await api.agent.triage(
        'new-ticket',
        title,
        description,
        labels.map((l) => l.name), // existing labels for the board
        projectContext,
        boardContext
      );
      setTriageResult(result);

      // Auto-apply suggestions
      if (result.priority) {
        setPriority(result.priority as Priority);
      }
      if (result.effort) {
        setEffort(result.effort as Effort);
      }
      if (result.labels && result.labels.length > 0) {
        // Match labels by name
        const matchedLabelIds = labels
          .filter((l) => result.labels?.includes(l.name))
          .map((l) => l.id);
        if (matchedLabelIds.length > 0) {
          setSelectedLabels(matchedLabelIds);
        }
      }
    } catch (error) {
      console.error('Triage failed:', error);
    } finally {
      setIsTriaging(false);
    }
  }, [title, description, labels, getAgentProjectContext, getAgentBoardContext, currentBoardId, board, columns, tickets]);

  // Toggle label selection
  const handleToggleLabel = useCallback((labelId: string) => {
    setSelectedLabels((prev) =>
      prev.includes(labelId)
        ? prev.filter((id) => id !== labelId)
        : [...prev, labelId]
    );
  }, []);

  // Submit form
  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();

      if (!title.trim() || !columnId || isSubmitting) return;

      setIsSubmitting(true);

      try {
        await addTicket({
          title: title.trim(),
          description: description.trim() || undefined,
          columnId,
          priority,
          effort,
          labels: selectedLabels.length > 0 ? selectedLabels : undefined,
          dueDate: dueDate || undefined,
        });

        onClose();
      } catch {
        // Error handled by store with toast
      } finally {
        setIsSubmitting(false);
      }
    },
    [title, description, columnId, priority, effort, selectedLabels, dueDate, isSubmitting, addTicket, onClose]
  );

  // Get sorted columns
  const sortedColumns = [...columns].sort((a, b) => a.position - b.position);

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm"
            onClick={onClose}
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
            className="fixed inset-0 z-50 flex items-start justify-center pt-[10vh] px-4 pointer-events-none"
          >
            <div
              className={cn(
                'w-full max-w-xl pointer-events-auto',
                'bg-bg-secondary border border-border-subtle rounded-xl shadow-2xl',
                'max-h-[80vh] overflow-hidden flex flex-col'
              )}
              onClick={(e) => e.stopPropagation()}
            >
              {/* Header */}
              <div className="flex items-center justify-between px-5 py-4 border-b border-border-subtle">
                <h2 className="text-lg font-semibold text-text-primary">
                  Create New Ticket
                </h2>
                <button
                  onClick={onClose}
                  className="p-1.5 rounded-lg text-text-tertiary hover:text-text-secondary hover:bg-bg-hover transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Form */}
              <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto">
                <div className="p-5 space-y-5">
                  {/* Title */}
                  <div>
                    <label
                      htmlFor="ticket-title"
                      className="block text-xs font-semibold uppercase tracking-wide text-text-muted mb-2"
                    >
                      Title <span className="text-status-error">*</span>
                    </label>
                    <input
                      ref={titleInputRef}
                      id="ticket-title"
                      type="text"
                      value={title}
                      onChange={(e) => setTitle(e.target.value)}
                      placeholder="What needs to be done?"
                      className={cn(
                        'w-full px-4 py-2.5',
                        'bg-bg-tertiary border border-border-subtle rounded-lg',
                        'text-sm text-text-primary placeholder:text-text-muted',
                        'focus:outline-none focus:border-accent focus:ring-2 focus:ring-accent/20'
                      )}
                      autoComplete="off"
                      maxLength={200}
                    />
                  </div>

                  {/* Description */}
                  <div>
                    <label
                      htmlFor="ticket-description"
                      className="block text-xs font-semibold uppercase tracking-wide text-text-muted mb-2"
                    >
                      Description
                    </label>
                    <textarea
                      id="ticket-description"
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      placeholder="Add more details..."
                      rows={3}
                      className={cn(
                        'w-full px-4 py-2.5',
                        'bg-bg-tertiary border border-border-subtle rounded-lg',
                        'text-sm text-text-primary placeholder:text-text-muted',
                        'focus:outline-none focus:border-accent focus:ring-2 focus:ring-accent/20',
                        'resize-none'
                      )}
                    />
                  </div>

                  {/* AI Triage Button */}
                  {title.trim() && (
                    <button
                      type="button"
                      onClick={handleAITriage}
                      disabled={isTriaging}
                      className={cn(
                        'w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg',
                        'bg-gradient-to-r from-indigo-500/20 to-purple-500/20',
                        'border border-indigo-500/30',
                        'text-sm font-medium text-indigo-400',
                        'hover:from-indigo-500/30 hover:to-purple-500/30 transition-all',
                        'disabled:opacity-50 disabled:cursor-not-allowed'
                      )}
                    >
                      {isTriaging ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin" />
                          <span>Analyzing...</span>
                        </>
                      ) : (
                        <>
                          <Sparkles className="w-4 h-4" />
                          <span>AI Auto-Fill</span>
                        </>
                      )}
                    </button>
                  )}

                  {/* AI Suggestion */}
                  {triageResult && (
                    <div className="p-3 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-xs text-indigo-300">
                      <strong>AI Suggestion:</strong> {triageResult.reasoning}
                    </div>
                  )}

                  {/* Column Selection */}
                  <div>
                    <label className="block text-xs font-semibold uppercase tracking-wide text-text-muted mb-2">
                      Column <span className="text-status-error">*</span>
                    </label>
                    <div className="flex flex-wrap gap-2">
                      {sortedColumns.map((col) => (
                        <button
                          key={col.id}
                          type="button"
                          onClick={() => setColumnId(col.id)}
                          className={cn(
                            'px-3 py-1.5 rounded-lg text-sm font-medium transition-colors',
                            'flex items-center gap-2',
                            columnId === col.id
                              ? 'bg-accent text-white'
                              : 'bg-bg-tertiary text-text-secondary hover:bg-bg-hover'
                          )}
                        >
                          <span
                            className="w-2 h-2 rounded-full"
                            style={{ backgroundColor: col.color || '#71717a' }}
                          />
                          {col.name}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Priority & Effort Row */}
                  <div className="grid grid-cols-2 gap-4">
                    {/* Priority */}
                    <div>
                      <label className="block text-xs font-semibold uppercase tracking-wide text-text-muted mb-2">
                        Priority
                      </label>
                      <div className="flex flex-wrap gap-1.5">
                        {PRIORITY_OPTIONS.map((opt) => (
                          <button
                            key={opt.value}
                            type="button"
                            onClick={() =>
                              setPriority(priority === opt.value ? undefined : opt.value)
                            }
                            className={cn(
                              'px-2 py-1 rounded text-xs font-medium transition-colors',
                              priority === opt.value
                                ? 'bg-accent text-white'
                                : 'bg-bg-tertiary text-text-secondary hover:bg-bg-hover'
                            )}
                          >
                            {opt.emoji} {opt.label}
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Effort */}
                    <div>
                      <label className="block text-xs font-semibold uppercase tracking-wide text-text-muted mb-2">
                        Effort
                      </label>
                      <div className="flex gap-1.5">
                        {EFFORT_OPTIONS.map((opt) => (
                          <button
                            key={opt.value}
                            type="button"
                            onClick={() =>
                              setEffort(effort === opt.value ? undefined : opt.value)
                            }
                            className={cn(
                              'px-2.5 py-1 rounded text-xs font-medium transition-colors',
                              effort === opt.value
                                ? 'bg-accent text-white'
                                : 'bg-bg-tertiary text-text-secondary hover:bg-bg-hover'
                            )}
                          >
                            {opt.label}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Labels */}
                  {labels.length > 0 && (
                    <div>
                      <label className="block text-xs font-semibold uppercase tracking-wide text-text-muted mb-2">
                        Labels
                      </label>
                      <div className="flex flex-wrap gap-2">
                        {labels.map((label) => (
                          <button
                            key={label.id}
                            type="button"
                            onClick={() => handleToggleLabel(label.id)}
                            className={cn(
                              'px-2.5 py-1 rounded-full text-xs font-medium transition-all',
                              'flex items-center gap-1.5',
                              selectedLabels.includes(label.id)
                                ? 'ring-2 ring-offset-1 ring-offset-bg-secondary'
                                : 'opacity-60 hover:opacity-100'
                            )}
                            style={{
                              backgroundColor: `${label.color}20`,
                              color: label.color,
                              ...(selectedLabels.includes(label.id) && {
                                ringColor: label.color,
                              }),
                            }}
                          >
                            <span
                              className="w-2 h-2 rounded-full"
                              style={{ backgroundColor: label.color }}
                            />
                            {label.name}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Due Date */}
                  <div>
                    <label
                      htmlFor="ticket-due-date"
                      className="block text-xs font-semibold uppercase tracking-wide text-text-muted mb-2"
                    >
                      Due Date
                    </label>
                    <input
                      id="ticket-due-date"
                      type="date"
                      value={dueDate}
                      onChange={(e) => setDueDate(e.target.value)}
                      className={cn(
                        'w-full px-4 py-2.5',
                        'bg-bg-tertiary border border-border-subtle rounded-lg',
                        'text-sm text-text-primary',
                        'focus:outline-none focus:border-accent focus:ring-2 focus:ring-accent/20'
                      )}
                    />
                  </div>
                </div>

                {/* Footer */}
                <div className="flex justify-end gap-3 px-5 py-4 border-t border-border-subtle bg-bg-primary">
                  <button
                    type="button"
                    onClick={onClose}
                    className={cn(
                      'px-4 py-2 rounded-lg text-sm font-medium',
                      'text-text-secondary hover:text-text-primary',
                      'hover:bg-bg-hover transition-colors'
                    )}
                    disabled={isSubmitting}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={!title.trim() || !columnId || isSubmitting}
                    className={cn(
                      'px-4 py-2 rounded-lg text-sm font-medium',
                      'bg-accent text-white',
                      'hover:bg-accent-hover transition-colors',
                      'disabled:opacity-50 disabled:cursor-not-allowed',
                      'flex items-center gap-2'
                    )}
                  >
                    {isSubmitting && <Loader2 className="w-4 h-4 animate-spin" />}
                    {isSubmitting ? 'Creating...' : 'Create Ticket'}
                  </button>
                </div>
              </form>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
});
