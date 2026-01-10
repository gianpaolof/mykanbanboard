// components/kanban/KanbanBoard.tsx
import { useState, useCallback } from 'react';
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
import type { Ticket } from '@/types';

export function KanbanBoard() {
  const { board, tickets, moveTicket, setTickets } = useBoardStore();
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

  if (!board) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-zinc-500">Loading board...</div>
      </div>
    );
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
        <div className="flex gap-4 h-full overflow-x-auto p-4">
          {board.columns
            .sort((a, b) => a.position - b.position)
            .map((column) => (
              <KanbanColumn
                key={column.id}
                column={column}
                tickets={tickets[column.id] || []}
                onTicketClick={setSelectedTicket}
                onAddTicket={() => {
                  // TODO: Open create ticket modal
                }}
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
          onClose={() => setSelectedTicket(null)}
        />
      )}
    </>
  );
}
