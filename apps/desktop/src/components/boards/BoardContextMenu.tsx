// components/boards/BoardContextMenu.tsx - Context menu for board actions
import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MoreHorizontal, Pencil, Trash2, Copy } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useBoardStore } from '@/stores/boardStore';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import type { BoardListItem } from '@/types';

interface BoardContextMenuProps {
  board: BoardListItem;
  onRename: () => void;
}

export function BoardContextMenu({ board, onRename }: BoardContextMenuProps) {
  const deleteBoard = useBoardStore((state) => state.deleteBoard);
  const createBoard = useBoardStore((state) => state.createBoard);
  const boards = useBoardStore((state) => state.boards);

  const [isOpen, setIsOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);

  // Close on click outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (
        menuRef.current &&
        !menuRef.current.contains(e.target as Node) &&
        buttonRef.current &&
        !buttonRef.current.contains(e.target as Node)
      ) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isOpen]);

  // Close on escape
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      window.addEventListener('keydown', handleKeyDown);
      return () => window.removeEventListener('keydown', handleKeyDown);
    }
  }, [isOpen]);

  const handleDuplicate = async () => {
    setIsOpen(false);
    await createBoard({
      name: `${board.name} (Copy)`,
    });
  };

  const handleDeleteClick = () => {
    if (boards.length <= 1) {
      setIsOpen(false);
      return;
    }
    setIsOpen(false);
    setShowDeleteConfirm(true);
  };

  const handleDeleteConfirm = async () => {
    setIsDeleting(true);
    try {
      await deleteBoard(board.id);
      setShowDeleteConfirm(false);
    } finally {
      setIsDeleting(false);
    }
  };

  const handleRename = () => {
    setIsOpen(false);
    onRename();
  };

  const canDelete = boards.length > 1;

  return (
    <>
      <div className="relative">
        <button
          ref={buttonRef}
          onClick={(e) => {
            e.stopPropagation();
            setIsOpen(!isOpen);
          }}
          className={cn(
            'p-1 rounded opacity-0 group-hover:opacity-100',
            'text-text-tertiary hover:text-text-secondary hover:bg-bg-hover',
            'transition-all',
            isOpen && 'opacity-100'
          )}
        >
          <MoreHorizontal className="w-4 h-4" />
        </button>

        <AnimatePresence>
          {isOpen && (
            <motion.div
              ref={menuRef}
              initial={{ opacity: 0, y: -4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -4 }}
              transition={{ duration: 0.1 }}
              className={cn(
                'absolute right-0 top-full mt-1 z-50',
                'w-40 p-1',
                'bg-bg-elevated border border-border-subtle rounded-lg shadow-xl'
              )}
            >
              {/* Rename */}
              <button
                onClick={handleRename}
                className={cn(
                  'w-full flex items-center gap-2 px-3 py-2 rounded-md',
                  'text-sm text-text-secondary',
                  'hover:bg-bg-hover hover:text-text-primary',
                  'transition-colors'
                )}
              >
                <Pencil className="w-4 h-4" />
                <span>Rename</span>
              </button>

              {/* Duplicate */}
              <button
                onClick={handleDuplicate}
                className={cn(
                  'w-full flex items-center gap-2 px-3 py-2 rounded-md',
                  'text-sm text-text-secondary',
                  'hover:bg-bg-hover hover:text-text-primary',
                  'transition-colors'
                )}
              >
                <Copy className="w-4 h-4" />
                <span>Duplicate</span>
              </button>

              {/* Divider */}
              <div className="my-1 border-t border-border-subtle" />

              {/* Delete */}
              <button
                onClick={handleDeleteClick}
                disabled={!canDelete}
                className={cn(
                  'w-full flex items-center gap-2 px-3 py-2 rounded-md',
                  'text-sm',
                  canDelete
                    ? 'text-status-error hover:bg-status-error/10'
                    : 'text-text-muted cursor-not-allowed',
                  'transition-colors'
                )}
              >
                <Trash2 className="w-4 h-4" />
                <span>Delete</span>
              </button>

              {!canDelete && (
                <p className="px-3 py-1.5 text-2xs text-text-muted">
                  Cannot delete the last board
                </p>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={showDeleteConfirm}
        onClose={() => setShowDeleteConfirm(false)}
        onConfirm={handleDeleteConfirm}
        title={`Delete "${board.name}"?`}
        message={`This will permanently delete this board and all its columns and tickets. This action cannot be undone.`}
        confirmText="Delete Board"
        cancelText="Cancel"
        variant="danger"
        isLoading={isDeleting}
      />
    </>
  );
}
