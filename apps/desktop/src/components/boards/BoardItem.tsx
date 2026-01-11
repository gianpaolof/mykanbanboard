// components/boards/BoardItem.tsx - Individual board item in sidebar
import { useState, useRef, useEffect, useCallback, memo } from 'react';
import { LayoutGrid, Check, X } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useBoardStore } from '@/stores/boardStore';
import { BoardContextMenu } from './BoardContextMenu';
import type { BoardListItem } from '@/types';

interface BoardItemProps {
  board: BoardListItem;
  isActive: boolean;
  onSelect: () => void;
}

export const BoardItem = memo(function BoardItem({
  board,
  isActive,
  onSelect,
}: BoardItemProps) {
  const updateBoard = useBoardStore((state) => state.updateBoard);

  const [isEditing, setIsEditing] = useState(false);
  const [editName, setEditName] = useState(board.name);
  const inputRef = useRef<HTMLInputElement>(null);

  // Focus input when editing
  useEffect(() => {
    if (isEditing) {
      inputRef.current?.focus();
      inputRef.current?.select();
    }
  }, [isEditing]);

  const handleStartRename = useCallback(() => {
    setEditName(board.name);
    setIsEditing(true);
  }, [board.name]);

  const handleCancelRename = useCallback(() => {
    setIsEditing(false);
    setEditName(board.name);
  }, [board.name]);

  const handleSubmitRename = useCallback(async () => {
    const trimmedName = editName.trim();
    if (trimmedName && trimmedName !== board.name) {
      await updateBoard(board.id, { name: trimmedName });
    }
    setIsEditing(false);
  }, [editName, board.id, board.name, updateBoard]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        handleSubmitRename();
      } else if (e.key === 'Escape') {
        e.preventDefault();
        handleCancelRename();
      }
    },
    [handleSubmitRename, handleCancelRename]
  );

  return (
    <div
      className={cn(
        'group flex items-center gap-2 px-2.5 py-2 rounded-md cursor-pointer transition-colors',
        isActive
          ? 'bg-accent-muted text-indigo-500 dark:text-indigo-400'
          : 'text-text-tertiary hover:bg-bg-hover hover:text-text-secondary'
      )}
      onClick={() => !isEditing && onSelect()}
    >
      <LayoutGrid className="w-4 h-4 flex-shrink-0" />

      {isEditing ? (
        <div className="flex-1 flex items-center gap-1.5">
          <input
            ref={inputRef}
            type="text"
            value={editName}
            onChange={(e) => setEditName(e.target.value)}
            onKeyDown={handleKeyDown}
            onBlur={handleSubmitRename}
            className={cn(
              'flex-1 px-1.5 py-0.5 text-sm font-medium',
              'bg-bg-tertiary border border-accent rounded',
              'text-text-primary outline-none'
            )}
            maxLength={50}
            onClick={(e) => e.stopPropagation()}
          />
          <button
            onClick={(e) => {
              e.stopPropagation();
              handleSubmitRename();
            }}
            className="p-0.5 text-status-success hover:bg-status-success/20 rounded"
          >
            <Check className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation();
              handleCancelRename();
            }}
            className="p-0.5 text-status-error hover:bg-status-error/20 rounded"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      ) : (
        <>
          <span className="flex-1 text-sm font-medium truncate">{board.name}</span>
          {board.ticketCount !== undefined && board.ticketCount > 0 && (
            <span
              className={cn(
                'px-1.5 py-0.5 text-2xs font-semibold rounded-md flex-shrink-0',
                isActive
                  ? 'bg-indigo-500/20 text-indigo-500 dark:text-indigo-400'
                  : 'bg-bg-tertiary text-text-tertiary'
              )}
            >
              {board.ticketCount}
            </span>
          )}
          <BoardContextMenu board={board} onRename={handleStartRename} />
        </>
      )}
    </div>
  );
});
