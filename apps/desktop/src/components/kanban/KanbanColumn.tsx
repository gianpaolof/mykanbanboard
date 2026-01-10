// components/kanban/KanbanColumn.tsx
import { useDroppable } from '@dnd-kit/core';
import { SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable';
import { AnimatePresence, motion } from 'framer-motion';
import { Plus, MoreHorizontal } from 'lucide-react';
import { cn } from '@/lib/utils';
import { TicketCard } from './TicketCard';
import type { Column, Ticket } from '@/types';

interface KanbanColumnProps {
  column: Column;
  tickets: Ticket[];
  onTicketClick?: (ticket: Ticket) => void;
  onAddTicket?: () => void;
}

export function KanbanColumn({ 
  column, 
  tickets, 
  onTicketClick,
  onAddTicket 
}: KanbanColumnProps) {
  const { setNodeRef, isOver } = useDroppable({
    id: column.id,
  });

  const ticketIds = tickets.map((t) => t.id);

  return (
    <div className="w-[300px] flex-shrink-0 flex flex-col max-h-full">
      {/* Column Header */}
      <div className="flex items-center justify-between px-1 py-2 mb-3">
        <div className="flex items-center gap-2">
          {/* Color dot */}
          <span
            className="w-2.5 h-2.5 rounded-full"
            style={{ backgroundColor: column.color || '#71717a' }}
          />
          
          {/* Title */}
          <h2 className="font-semibold text-sm text-zinc-100">
            {column.name}
          </h2>
          
          {/* Count */}
          <span className="text-xs text-zinc-500 bg-zinc-800 px-2 py-0.5 rounded">
            {tickets.length}
            {column.wipLimit && `/${column.wipLimit}`}
          </span>
        </div>

        {/* Actions */}
        <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <button
            onClick={onAddTicket}
            className={cn(
              'w-6 h-6 rounded flex items-center justify-center',
              'text-zinc-500 hover:text-zinc-100 hover:bg-white/5',
              'transition-colors'
            )}
          >
            <Plus className="w-3.5 h-3.5" />
          </button>
          <button
            className={cn(
              'w-6 h-6 rounded flex items-center justify-center',
              'text-zinc-500 hover:text-zinc-100 hover:bg-white/5',
              'transition-colors'
            )}
          >
            <MoreHorizontal className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Cards Container */}
      <div
        ref={setNodeRef}
        className={cn(
          'flex-1 overflow-y-auto pr-1',
          'min-h-[100px]',
          // Drop indicator
          isOver && 'bg-indigo-500/5 rounded-lg'
        )}
      >
        <SortableContext items={ticketIds} strategy={verticalListSortingStrategy}>
          <motion.div 
            className="flex flex-col gap-2"
            initial="hidden"
            animate="visible"
            variants={{
              hidden: { opacity: 0 },
              visible: {
                opacity: 1,
                transition: { staggerChildren: 0.05 }
              }
            }}
          >
            <AnimatePresence mode="popLayout">
              {tickets.map((ticket) => (
                <TicketCard
                  key={ticket.id}
                  ticket={ticket}
                  onClick={() => onTicketClick?.(ticket)}
                />
              ))}
            </AnimatePresence>
          </motion.div>
        </SortableContext>

        {/* Add Ticket Button */}
        <button
          onClick={onAddTicket}
          className={cn(
            'w-full mt-2 py-2 px-3',
            'flex items-center gap-2',
            'rounded-lg border border-dashed border-zinc-700',
            'text-zinc-500 text-sm',
            'hover:border-indigo-500 hover:text-indigo-400 hover:bg-indigo-500/10',
            'transition-all duration-200'
          )}
        >
          <Plus className="w-4 h-4" />
          <span>Add ticket</span>
        </button>
      </div>
    </div>
  );
}
