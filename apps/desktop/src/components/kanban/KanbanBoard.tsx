// components/kanban/KanbanBoard.tsx
import { useState, useCallback, useMemo, memo } from 'react';
import {
  DndContext,
  DragEndEvent,
  DragOverEvent,
  DragOverlay,
  DragStartEvent,
  PointerSensor,
  useSensor,
  useSensors,
  closestCorners,
} from '@dnd-kit/core';
import { arrayMove } from '@dnd-kit/sortable';
import { useBoardStore } from '@/stores/boardStore';
import { KanbanColumn } from './KanbanColumn';
import { TicketCard } from './TicketCard';
import { TicketModal } from './TicketModal';
import { BoardSkeleton } from './BoardSkeleton';
import type { Ticket } from '@/types';

interface KanbanBoardProps {
  onAddTicket?: (columnId: string) => void;
  filteredTickets?: Record<string, Ticket[]>;
}

export const KanbanBoard = memo(function KanbanBoard({ onAddTicket, filteredTickets }: KanbanBoardProps) {
  const { board, tickets, moveTicket, setTickets, deleteTicket } = useBoardStore();

  // Use filtered tickets if provided, otherwise use all tickets
  const displayTickets = filteredTickets || tickets;
  const [activeTicket, setActiveTicket] = useState<Ticket | null>(null);
  const [selectedTicket, setSelectedTicket] = useState<Ticket | null>(null);

  // Configure drag sensors
  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8, // 8px movement before drag starts
      },
    })
  );

  // Handle drag start
  const handleDragStart = useCallback((event: DragStartEvent) => {
    const { active } = event;
    const ticketId = active.id as string;

    // Find the ticket being dragged
    for (const columnTickets of Object.values(tickets)) {
      const ticket = columnTickets.find((t) => t.id === ticketId);
      if (ticket) {
        setActiveTicket(ticket);
        break;
      }
    }
  }, [tickets]);

  // Handle drag over (for column changes)
  const handleDragOver = useCallback((event: DragOverEvent) => {
    const { active, over } = event;
    if (!over) return;

    const activeId = active.id as string;
    const overId = over.id as string;

    // Find source and destination columns
    let sourceColumnId: string | null = null;
    let destColumnId: string | null = null;

    for (const [columnId, columnTickets] of Object.entries(tickets)) {
      if (columnTickets.find((t) => t.id === activeId)) {
        sourceColumnId = columnId;
      }
      if (columnId === overId || columnTickets.find((t) => t.id === overId)) {
        destColumnId = columnId === overId ? columnId : columnId;
      }
    }

    // If dropping on a column (not a ticket)
    if (board?.columns.find((c) => c.id === overId)) {
      destColumnId = overId;
    }

    if (!sourceColumnId || !destColumnId || sourceColumnId === destColumnId) {
      return;
    }

    // Move ticket to new column optimistically
    const sourceTickets = [...tickets[sourceColumnId]];
    const destTickets = [...(tickets[destColumnId] || [])];

    const ticketIndex = sourceTickets.findIndex((t) => t.id === activeId);
    if (ticketIndex === -1) return;

    const [movedTicket] = sourceTickets.splice(ticketIndex, 1);
    destTickets.push({ ...movedTicket, columnId: destColumnId });

    setTickets(sourceColumnId, sourceTickets);
    setTickets(destColumnId, destTickets);
  }, [tickets, board, setTickets]);

  // Handle drag end
  const handleDragEnd = useCallback((event: DragEndEvent) => {
    const { active, over } = event;
    setActiveTicket(null);

    if (!over) return;

    const activeId = active.id as string;
    const overId = over.id as string;

    // Find which column the ticket is now in
    let targetColumnId: string | null = null;
    let position = 0;

    for (const [columnId, columnTickets] of Object.entries(tickets)) {
      const ticketIndex = columnTickets.findIndex((t) => t.id === activeId);
      if (ticketIndex !== -1) {
        targetColumnId = columnId;

        // Calculate new position
        if (overId !== activeId) {
          const overIndex = columnTickets.findIndex((t) => t.id === overId);
          if (overIndex !== -1) {
            position = overIndex;
          }
        }
        break;
      }
    }

    if (targetColumnId) {
      // Reorder within column if needed
      const columnTickets = tickets[targetColumnId];
      const oldIndex = columnTickets.findIndex((t) => t.id === activeId);
      const newIndex = columnTickets.findIndex((t) => t.id === overId);

      if (oldIndex !== newIndex && newIndex !== -1) {
        const reordered = arrayMove(columnTickets, oldIndex, newIndex);
        setTickets(targetColumnId, reordered);
        position = newIndex;
      }

      // Persist to backend
      moveTicket({
        ticketId: activeId,
        targetColumnId,
        position,
      });
    }
  }, [tickets, moveTicket, setTickets]);

  // Memoize sorted columns to avoid re-sorting on every render
  const sortedColumns = useMemo(() => {
    if (!board) return [];
    return [...board.columns].sort((a, b) => a.position - b.position);
  }, [board]);

  // Memoize onTicketClick handler
  const handleTicketClick = useCallback((ticket: Ticket) => {
    setSelectedTicket(ticket);
  }, []);

  // Memoize onDelete handler
  const handleDelete = useCallback(async () => {
    if (selectedTicket) {
      await deleteTicket(selectedTicket.id);
      setSelectedTicket(null);
    }
  }, [selectedTicket, deleteTicket]);

  // Memoize onClose handler
  const handleCloseModal = useCallback(() => {
    setSelectedTicket(null);
  }, []);

  if (!board) {
    return <BoardSkeleton />;
  }

  return (
    <>
      <DndContext
        sensors={sensors}
        collisionDetection={closestCorners}
        onDragStart={handleDragStart}
        onDragOver={handleDragOver}
        onDragEnd={handleDragEnd}
      >
        <div className="flex items-start gap-4 h-full overflow-x-auto overflow-y-hidden p-4 pb-6 scrollbar-thin">
          {sortedColumns.map((column) => (
            <KanbanColumn
              key={column.id}
              column={column}
              tickets={displayTickets[column.id] || []}
              onTicketClick={handleTicketClick}
              onAddTicket={() => onAddTicket?.(column.id)}
            />
          ))}
        </div>

        {/* Drag Overlay - shows the card being dragged */}
        <DragOverlay>
          {activeTicket && (
            <TicketCard ticket={activeTicket} isDragging />
          )}
        </DragOverlay>
      </DndContext>

      {/* Ticket Detail Modal */}
      {selectedTicket && (
        <TicketModal
          ticket={selectedTicket}
          onClose={handleCloseModal}
          onDelete={handleDelete}
        />
      )}
    </>
  );
});
