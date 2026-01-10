// components/kanban/TicketCard.tsx
import { memo, useMemo } from 'react';
import { motion } from 'framer-motion';
import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { Calendar, MessageSquare, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { Ticket } from '@/types';

interface TicketCardProps {
  ticket: Ticket;
  onClick?: () => void;
  isDragging?: boolean;
}

// Move constants outside component to avoid recreation
const priorityColors = {
  critical: 'bg-red-500 shadow-red-500/50 shadow-[0_0_8px]',
  high: 'bg-orange-500 shadow-orange-500/50 shadow-[0_0_8px]',
  medium: 'bg-yellow-500',
  low: 'bg-green-500',
} as const;

const labelColors: Record<string, string> = {
  red: 'bg-red-500/15 text-red-300',
  blue: 'bg-blue-500/15 text-blue-300',
  green: 'bg-green-500/15 text-green-300',
  yellow: 'bg-yellow-500/15 text-yellow-300',
  purple: 'bg-purple-500/15 text-purple-300',
  pink: 'bg-pink-500/15 text-pink-300',
};

// Date formatter singleton - avoid recreation
const dateFormatter = new Intl.DateTimeFormat('en', {
  month: 'short',
  day: 'numeric'
});

function formatDate(date: Date | string): string {
  return dateFormatter.format(new Date(date));
}

export const TicketCard = memo(function TicketCard({
  ticket,
  onClick,
  isDragging
}: TicketCardProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
  } = useSortable({ id: ticket.id });

  const style = useMemo(() => ({
    transform: CSS.Transform.toString(transform),
    transition,
  }), [transform, transition]);

  const isOverdue = useMemo(() => {
    if (!ticket.dueDate) return false;
    return new Date(ticket.dueDate) < new Date();
  }, [ticket.dueDate]);

  const visibleLabels = useMemo(() =>
    ticket.labels.slice(0, 3),
    [ticket.labels]
  );

  return (
    <motion.div
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      whileHover={{ y: -2 }}
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      className={cn(
        // Glass effect
        'bg-white/[0.04] backdrop-blur-xl',
        'border border-white/[0.08]',
        'rounded-xl p-3',
        // Interaction
        'cursor-grab active:cursor-grabbing',
        'transition-all duration-200',
        // Hover
        'hover:bg-white/[0.07] hover:border-white/[0.12]',
        'hover:shadow-lg hover:shadow-black/20',
        // Dragging
        isDragging && 'opacity-50 scale-105 shadow-xl',
      )}
    >
      {/* Header: Priority + Labels */}
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          {ticket.priority && (
            <span
              className={cn(
                'w-2 h-2 rounded-full',
                priorityColors[ticket.priority]
              )}
            />
          )}
        </div>

        {visibleLabels.length > 0 && (
          <div className="flex gap-1 flex-wrap justify-end">
            {visibleLabels.map((label) => (
              <span
                key={label.id}
                className={cn(
                  'text-[10px] font-semibold uppercase tracking-wide',
                  'px-1.5 py-0.5 rounded',
                  labelColors[label.color] || 'bg-zinc-500/15 text-zinc-300'
                )}
              >
                {label.name}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Title */}
      <h3 className="font-semibold text-sm leading-snug mb-3 text-zinc-100">
        {ticket.title}
      </h3>

      {/* Footer: Meta + Effort */}
      <div className="flex items-center justify-between text-xs text-zinc-500">
        <div className="flex items-center gap-3">
          {ticket.dueDate && (
            <span className={cn(
              'flex items-center gap-1',
              isOverdue && 'text-red-400'
            )}>
              {isOverdue ? (
                <AlertCircle className="w-3 h-3" />
              ) : (
                <Calendar className="w-3 h-3" />
              )}
              {isOverdue ? 'Overdue' : formatDate(ticket.dueDate)}
            </span>
          )}

          {ticket.comments.length > 0 && (
            <span className="flex items-center gap-1">
              <MessageSquare className="w-3 h-3" />
              {ticket.comments.length}
            </span>
          )}
        </div>

        {ticket.effort && (
          <span className="font-mono text-[10px] bg-zinc-800 px-1.5 py-0.5 rounded text-zinc-400">
            {ticket.effort.toUpperCase()}
          </span>
        )}
      </div>
    </motion.div>
  );
}, (prevProps, nextProps) => {
  // Custom comparison for better memoization
  return (
    prevProps.ticket.id === nextProps.ticket.id &&
    prevProps.ticket.title === nextProps.ticket.title &&
    prevProps.ticket.priority === nextProps.ticket.priority &&
    prevProps.ticket.effort === nextProps.ticket.effort &&
    prevProps.ticket.dueDate === nextProps.ticket.dueDate &&
    prevProps.ticket.labels.length === nextProps.ticket.labels.length &&
    prevProps.ticket.comments.length === nextProps.ticket.comments.length &&
    prevProps.isDragging === nextProps.isDragging &&
    prevProps.onClick === nextProps.onClick
  );
});
