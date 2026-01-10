// components/kanban/TicketModal.tsx
import { motion, AnimatePresence } from 'framer-motion';
import { X, Sparkles, GitBranch, Trash2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { Ticket } from '@/types';

interface TicketModalProps {
  ticket: Ticket;
  onClose: () => void;
  onSave?: (updates: Partial<Ticket>) => void;
  onDelete?: () => void;
  onAITriage?: () => void;
  onDecompose?: () => void;
}

export function TicketModal({ 
  ticket, 
  onClose,
  onSave,
  onDelete,
  onAITriage,
  onDecompose,
}: TicketModalProps) {
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
                defaultValue={ticket.description}
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

            {/* Fields Grid */}
            <div className="grid grid-cols-2 gap-4">
              {/* Priority */}
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wide text-zinc-500 mb-2">
                  Priority
                </label>
                <select
                  defaultValue={ticket.priority || 'medium'}
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
                  defaultValue={ticket.effort || 'm'}
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
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between p-4 border-t border-zinc-800">
            <div className="flex gap-2">
              {/* AI Actions */}
              <button
                onClick={onAITriage}
                className={cn(
                  'px-3 py-2 rounded-lg text-sm font-medium',
                  'bg-gradient-to-r from-indigo-500 to-purple-500 text-white',
                  'hover:shadow-lg hover:shadow-indigo-500/25',
                  'flex items-center gap-2 transition-all'
                )}
              >
                <Sparkles className="w-4 h-4" />
                AI Triage
              </button>
              <button
                onClick={onDecompose}
                className={cn(
                  'px-3 py-2 rounded-lg text-sm font-medium',
                  'bg-zinc-800 text-zinc-100 border border-zinc-700',
                  'hover:bg-zinc-700',
                  'flex items-center gap-2 transition-colors'
                )}
              >
                <GitBranch className="w-4 h-4" />
                Decompose
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
                onClick={() => onSave?.({})}
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
}
