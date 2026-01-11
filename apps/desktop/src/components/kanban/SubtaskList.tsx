// components/kanban/SubtaskList.tsx - Subtask checklist component
import { useState, useCallback, memo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, Trash2, GripVertical, Check } from 'lucide-react';
import { cn } from '@/lib/utils';
import { subtaskApi } from '@/lib/tauri';
import type { Subtask } from '@/types';

interface SubtaskListProps {
  ticketId: string;
  subtasks: Subtask[];
  onSubtasksChange: (subtasks: Subtask[]) => void;
}

export const SubtaskList = memo(function SubtaskList({
  ticketId,
  subtasks,
  onSubtasksChange,
}: SubtaskListProps) {
  const [newSubtaskTitle, setNewSubtaskTitle] = useState('');
  const [isAdding, setIsAdding] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState('');

  const completedCount = subtasks.filter((s) => s.completed).length;
  const progress = subtasks.length > 0 ? (completedCount / subtasks.length) * 100 : 0;

  const handleAddSubtask = useCallback(async () => {
    if (!newSubtaskTitle.trim()) return;

    setIsAdding(true);
    try {
      const newSubtask = await subtaskApi.createSubtask({
        parentTicketId: ticketId,
        title: newSubtaskTitle.trim(),
      });
      onSubtasksChange([...subtasks, newSubtask]);
      setNewSubtaskTitle('');
    } catch (error) {
      console.error('Failed to create subtask:', error);
    } finally {
      setIsAdding(false);
    }
  }, [ticketId, newSubtaskTitle, subtasks, onSubtasksChange]);

  const handleToggle = useCallback(
    async (subtaskId: string) => {
      try {
        const updated = await subtaskApi.toggleSubtask(subtaskId);
        onSubtasksChange(
          subtasks.map((s) => (s.id === subtaskId ? updated : s))
        );
      } catch (error) {
        console.error('Failed to toggle subtask:', error);
      }
    },
    [subtasks, onSubtasksChange]
  );

  const handleDelete = useCallback(
    async (subtaskId: string) => {
      try {
        await subtaskApi.deleteSubtask(subtaskId);
        onSubtasksChange(subtasks.filter((s) => s.id !== subtaskId));
      } catch (error) {
        console.error('Failed to delete subtask:', error);
      }
    },
    [subtasks, onSubtasksChange]
  );

  const handleStartEdit = useCallback((subtask: Subtask) => {
    setEditingId(subtask.id);
    setEditingTitle(subtask.title);
  }, []);

  const handleSaveEdit = useCallback(async () => {
    if (!editingId || !editingTitle.trim()) {
      setEditingId(null);
      return;
    }

    try {
      const updated = await subtaskApi.updateSubtask(editingId, {
        title: editingTitle.trim(),
      });
      onSubtasksChange(
        subtasks.map((s) => (s.id === editingId ? updated : s))
      );
    } catch (error) {
      console.error('Failed to update subtask:', error);
    } finally {
      setEditingId(null);
    }
  }, [editingId, editingTitle, subtasks, onSubtasksChange]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        if (editingId) {
          handleSaveEdit();
        } else {
          handleAddSubtask();
        }
      } else if (e.key === 'Escape') {
        setEditingId(null);
        setNewSubtaskTitle('');
      }
    },
    [editingId, handleSaveEdit, handleAddSubtask]
  );

  return (
    <div className="space-y-3">
      {/* Header with progress */}
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-medium text-text-secondary">
          Subtasks
          {subtasks.length > 0 && (
            <span className="ml-2 text-text-muted">
              ({completedCount}/{subtasks.length})
            </span>
          )}
        </h4>
      </div>

      {/* Progress bar */}
      {subtasks.length > 0 && (
        <div className="h-1.5 bg-bg-tertiary rounded-full overflow-hidden">
          <motion.div
            className="h-full bg-status-success rounded-full"
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.3, ease: 'easeOut' }}
          />
        </div>
      )}

      {/* Subtask list */}
      <div className="space-y-1">
        <AnimatePresence mode="popLayout">
          {subtasks.map((subtask) => (
            <motion.div
              key={subtask.id}
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.2 }}
              className="group"
            >
              <div
                className={cn(
                  'flex items-center gap-2 px-2 py-1.5 rounded-md',
                  'hover:bg-bg-hover transition-colors',
                  subtask.completed && 'opacity-60'
                )}
              >
                {/* Drag handle */}
                <GripVertical className="w-3.5 h-3.5 text-text-muted opacity-0 group-hover:opacity-100 cursor-grab" />

                {/* Checkbox */}
                <button
                  onClick={() => handleToggle(subtask.id)}
                  className={cn(
                    'flex-shrink-0 w-4 h-4 rounded border transition-all',
                    subtask.completed
                      ? 'bg-status-success border-status-success'
                      : 'border-border-DEFAULT hover:border-accent'
                  )}
                >
                  {subtask.completed && (
                    <Check className="w-3 h-3 text-white m-auto" />
                  )}
                </button>

                {/* Title */}
                {editingId === subtask.id ? (
                  <input
                    type="text"
                    value={editingTitle}
                    onChange={(e) => setEditingTitle(e.target.value)}
                    onBlur={handleSaveEdit}
                    onKeyDown={handleKeyDown}
                    autoFocus
                    className={cn(
                      'flex-1 bg-transparent text-sm text-text-primary',
                      'border-b border-accent focus:outline-none'
                    )}
                  />
                ) : (
                  <span
                    onClick={() => handleStartEdit(subtask)}
                    className={cn(
                      'flex-1 text-sm cursor-text',
                      subtask.completed
                        ? 'text-text-muted line-through'
                        : 'text-text-primary'
                    )}
                  >
                    {subtask.title}
                  </span>
                )}

                {/* Delete button */}
                <button
                  onClick={() => handleDelete(subtask.id)}
                  className={cn(
                    'p-1 rounded opacity-0 group-hover:opacity-100',
                    'text-text-muted hover:text-status-error hover:bg-status-error/10',
                    'transition-all'
                  )}
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      {/* Add subtask input */}
      <div className="flex items-center gap-2">
        <Plus className="w-4 h-4 text-text-muted" />
        <input
          type="text"
          value={newSubtaskTitle}
          onChange={(e) => setNewSubtaskTitle(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Add subtask..."
          disabled={isAdding}
          className={cn(
            'flex-1 bg-transparent text-sm text-text-primary',
            'placeholder:text-text-muted',
            'focus:outline-none',
            isAdding && 'opacity-50'
          )}
        />
        {newSubtaskTitle.trim() && (
          <button
            onClick={handleAddSubtask}
            disabled={isAdding}
            className={cn(
              'px-2 py-0.5 rounded text-xs font-medium',
              'bg-accent text-white',
              'hover:bg-accent-hover transition-colors',
              'disabled:opacity-50'
            )}
          >
            Add
          </button>
        )}
      </div>
    </div>
  );
});
