// components/boards/CreateBoardModal.tsx - Modal for creating new boards
import { useState, useCallback, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, LayoutGrid } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useBoardStore } from '@/stores/boardStore';

interface CreateBoardModalProps {
  isOpen: boolean;
  onClose: () => void;
  onBoardCreated?: (boardId: string) => void;
}

export function CreateBoardModal({
  isOpen,
  onClose,
  onBoardCreated,
}: CreateBoardModalProps) {
  const createBoard = useBoardStore((state) => state.createBoard);
  const switchBoard = useBoardStore((state) => state.switchBoard);

  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [isCreating, setIsCreating] = useState(false);

  const inputRef = useRef<HTMLInputElement>(null);

  // Focus input on open
  useEffect(() => {
    if (isOpen) {
      setName('');
      setDescription('');
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [isOpen]);

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

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();

      if (!name.trim() || isCreating) return;

      setIsCreating(true);

      try {
        const newBoard = await createBoard({
          name: name.trim(),
          description: description.trim() || undefined,
        });

        // Switch to the new board
        await switchBoard(newBoard.id);

        onBoardCreated?.(newBoard.id);
        onClose();
      } catch {
        // Error is already handled by the store with toast
      } finally {
        setIsCreating(false);
      }
    },
    [name, description, isCreating, createBoard, switchBoard, onBoardCreated, onClose]
  );

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
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{ duration: 0.15 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 pointer-events-none"
          >
            <div
              className={cn(
                'w-full max-w-md p-6 pointer-events-auto',
                'bg-bg-elevated border border-border-subtle rounded-xl shadow-2xl'
              )}
              onClick={(e) => e.stopPropagation()}
            >
              {/* Header */}
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-accent/20 flex items-center justify-center">
                    <LayoutGrid className="w-5 h-5 text-accent" />
                  </div>
                  <div>
                    <h2 className="text-lg font-semibold text-text-primary">
                      Create New Board
                    </h2>
                    <p className="text-xs text-text-muted">
                      Organize your work in a new board
                    </p>
                  </div>
                </div>
                <button
                  onClick={onClose}
                  className="p-2 rounded-lg text-text-tertiary hover:text-text-secondary hover:bg-bg-hover transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Form */}
              <form onSubmit={handleSubmit} className="space-y-4">
                {/* Name Field */}
                <div>
                  <label
                    htmlFor="board-name"
                    className="block text-xs font-semibold uppercase tracking-wide text-text-muted mb-2"
                  >
                    Board Name
                  </label>
                  <input
                    ref={inputRef}
                    id="board-name"
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="e.g., Product Roadmap"
                    className={cn(
                      'w-full px-4 py-2.5',
                      'bg-bg-tertiary border border-border-subtle rounded-lg',
                      'text-sm text-text-primary placeholder:text-text-muted',
                      'focus:outline-none focus:border-accent focus:ring-2 focus:ring-accent/20',
                      'transition-colors'
                    )}
                    maxLength={50}
                    autoComplete="off"
                  />
                </div>

                {/* Description Field */}
                <div>
                  <label
                    htmlFor="board-description"
                    className="block text-xs font-semibold uppercase tracking-wide text-text-muted mb-2"
                  >
                    Description{' '}
                    <span className="font-normal text-text-tertiary">(optional)</span>
                  </label>
                  <textarea
                    id="board-description"
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="What's this board for?"
                    rows={3}
                    className={cn(
                      'w-full px-4 py-2.5',
                      'bg-bg-tertiary border border-border-subtle rounded-lg',
                      'text-sm text-text-primary placeholder:text-text-muted',
                      'focus:outline-none focus:border-accent focus:ring-2 focus:ring-accent/20',
                      'transition-colors resize-none'
                    )}
                    maxLength={200}
                  />
                </div>

                {/* Actions */}
                <div className="flex justify-end gap-3 pt-2">
                  <button
                    type="button"
                    onClick={onClose}
                    className={cn(
                      'px-4 py-2 rounded-lg text-sm font-medium',
                      'text-text-secondary hover:text-text-primary',
                      'hover:bg-bg-hover transition-colors'
                    )}
                    disabled={isCreating}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={!name.trim() || isCreating}
                    className={cn(
                      'px-4 py-2 rounded-lg text-sm font-medium',
                      'bg-accent text-white',
                      'hover:bg-accent-hover transition-colors',
                      'disabled:opacity-50 disabled:cursor-not-allowed'
                    )}
                  >
                    {isCreating ? 'Creating...' : 'Create Board'}
                  </button>
                </div>
              </form>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
