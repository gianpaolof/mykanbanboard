// components/kanban/EmptyColumn.tsx - Empty state for columns without tickets
import { memo } from 'react';
import { motion } from 'framer-motion';
import { Inbox, Plus } from 'lucide-react';
import { cn } from '@/lib/utils';
import { fadeInUp } from '@/lib/animations';

interface EmptyColumnProps {
  columnName: string;
  onAddTicket?: () => void;
}

export const EmptyColumn = memo(function EmptyColumn({
  columnName,
  onAddTicket,
}: EmptyColumnProps) {
  return (
    <motion.div
      variants={fadeInUp}
      initial="hidden"
      animate="visible"
      className="flex flex-col items-center justify-center py-12 px-4 text-center"
    >
      {/* Glass card with icon */}
      <div
        className={cn(
          'w-16 h-16 rounded-2xl flex items-center justify-center mb-4',
          'bg-glass-bg border border-glass-border',
          'backdrop-blur-xl'
        )}
      >
        <Inbox className="w-8 h-8 text-text-muted" />
      </div>

      {/* Message */}
      <h3 className="text-sm font-medium text-text-secondary mb-1">
        No tickets in {columnName}
      </h3>
      <p className="text-xs text-text-muted max-w-[200px] mb-4">
        Drag tickets here or click the button below to add one
      </p>

      {/* Add button */}
      {onAddTicket && (
        <button
          onClick={onAddTicket}
          className={cn(
            'flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium',
            'bg-bg-hover text-text-tertiary',
            'hover:bg-bg-active hover:text-text-secondary',
            'transition-colors'
          )}
        >
          <Plus className="w-3.5 h-3.5" />
          Add ticket
        </button>
      )}
    </motion.div>
  );
});
