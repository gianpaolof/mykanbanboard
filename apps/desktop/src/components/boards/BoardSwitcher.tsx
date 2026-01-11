// components/boards/BoardSwitcher.tsx - Dropdown to switch between boards
import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, Plus, Check } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useBoardStore } from '@/stores/boardStore';

interface BoardSwitcherProps {
  onCreateBoard?: () => void;
  className?: string;
}

export function BoardSwitcher({ onCreateBoard, className }: BoardSwitcherProps) {
  const boards = useBoardStore((state) => state.boards);
  const currentBoardId = useBoardStore((state) => state.currentBoardId);
  const board = useBoardStore((state) => state.board);
  const switchBoard = useBoardStore((state) => state.switchBoard);
  const isSwitching = useBoardStore((state) => state.isSwitching);

  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);

  const currentBoard = board || boards.find((b) => b.id === currentBoardId);

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

  const handleSwitchBoard = async (boardId: string) => {
    if (boardId === currentBoardId) {
      setIsOpen(false);
      return;
    }
    setIsOpen(false);
    await switchBoard(boardId);
  };

  const handleCreateBoard = () => {
    setIsOpen(false);
    onCreateBoard?.();
  };

  // Sort boards alphabetically
  const sortedBoards = [...boards].sort((a, b) => a.name.localeCompare(b.name));

  return (
    <div className={cn('relative', className)}>
      {/* Trigger Button */}
      <button
        ref={buttonRef}
        onClick={() => setIsOpen(!isOpen)}
        disabled={isSwitching}
        className={cn(
          'flex items-center gap-2 px-2 py-1 -ml-2 rounded-md',
          'text-base font-semibold text-text-primary',
          'hover:bg-bg-hover transition-colors',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/50',
          isSwitching && 'opacity-70 cursor-wait'
        )}
      >
        <span className="truncate max-w-[200px]">
          {currentBoard?.name || 'Select Board'}
        </span>
        <ChevronDown
          className={cn(
            'w-4 h-4 text-text-tertiary transition-transform duration-200',
            isOpen && 'rotate-180'
          )}
        />
      </button>

      {/* Dropdown Menu */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            ref={menuRef}
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.15 }}
            className={cn(
              'absolute left-0 top-full mt-1 z-50',
              'w-64 py-1',
              'bg-bg-elevated border border-border-subtle rounded-lg shadow-xl'
            )}
          >
            {/* Board List */}
            <div className="max-h-64 overflow-y-auto">
              {sortedBoards.map((b) => (
                <button
                  key={b.id}
                  onClick={() => handleSwitchBoard(b.id)}
                  className={cn(
                    'w-full flex items-center justify-between px-3 py-2',
                    'text-sm text-left',
                    'hover:bg-bg-hover transition-colors',
                    b.id === currentBoardId
                      ? 'text-text-primary bg-bg-active'
                      : 'text-text-secondary'
                  )}
                >
                  <div className="flex-1 min-w-0">
                    <div className="truncate font-medium">{b.name}</div>
                    <div className="text-xs text-text-muted">
                      {b.ticketCount} ticket{b.ticketCount !== 1 ? 's' : ''}
                    </div>
                  </div>
                  {b.id === currentBoardId && (
                    <Check className="w-4 h-4 text-accent flex-shrink-0 ml-2" />
                  )}
                </button>
              ))}
            </div>

            {/* Divider */}
            <div className="my-1 border-t border-border-subtle" />

            {/* Create Board Button */}
            <button
              onClick={handleCreateBoard}
              className={cn(
                'w-full flex items-center gap-2 px-3 py-2',
                'text-sm text-text-secondary',
                'hover:bg-bg-hover hover:text-text-primary',
                'transition-colors'
              )}
            >
              <Plus className="w-4 h-4" />
              <span>Create new board</span>
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
