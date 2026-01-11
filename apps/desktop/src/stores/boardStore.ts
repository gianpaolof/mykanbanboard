import { create } from 'zustand';
import { toast } from 'sonner';
import type { Ticket, Column, Label, TicketCreate, TicketUpdate, ColumnCreate } from '@/types';
import { api } from '@/lib/tauri';

// ===========================================
// BOARD STORE
// ===========================================

interface BoardState {
  // Data
  columns: Column[];
  tickets: Record<string, Ticket[]>; // columnId -> tickets
  labels: Label[];

  // Board info
  board: {
    id: string;
    name: string;
    columns: Column[];
  } | null;

  // Loading states
  isLoading: boolean;
  error: string | null;

  // Actions - Columns
  setColumns: (columns: Column[]) => void;
  addColumn: (column: ColumnCreate) => Promise<void>;
  updateColumn: (id: string, updates: Partial<Column>) => Promise<void>;
  deleteColumn: (id: string) => Promise<void>;
  reorderColumns: (columnIds: string[]) => Promise<void>;

  // Actions - Tickets
  setTickets: (columnId: string, tickets: Ticket[]) => void;
  addTicket: (ticket: TicketCreate) => Promise<Ticket>;
  updateTicket: (id: string, updates: TicketUpdate) => Promise<void>;
  deleteTicket: (id: string) => Promise<void>;
  moveTicket: (params: { ticketId: string; targetColumnId: string; position: number }) => Promise<void>;

  // Actions - Labels
  setLabels: (labels: Label[]) => void;
  addLabel: (name: string, color: string) => Promise<Label>;
  deleteLabel: (id: string) => Promise<void>;

  // Actions - Load
  loadBoard: () => Promise<void>;
}

export const useBoardStore = create<BoardState>()((set, get) => ({
  // Initial state
  columns: [],
  tickets: {},
  labels: [],
  board: null,
  isLoading: false,
  error: null,

  // ===========================================
  // COLUMNS
  // ===========================================

  setColumns: (columns) => {
    set({ columns });
  },

  addColumn: async (column) => {
    const prevColumns = get().columns;
    const prevBoard = get().board;

    try {
      // Call backend
      const newColumn = await api.columns.createColumn(column);

      set((state) => ({
        columns: [...state.columns, newColumn],
        board: state.board ? {
          ...state.board,
          columns: [...state.board.columns, newColumn],
        } : null,
        tickets: { ...state.tickets, [newColumn.id]: [] },
      }));
    } catch (error) {
      // Rollback on error
      const errorMessage = error instanceof Error ? error.message : String(error);
      set({
        columns: prevColumns,
        board: prevBoard,
        error: errorMessage,
      });
      toast.error(`Failed to create column: ${errorMessage}`);
      throw error;
    }
  },

  updateColumn: async (id, updates) => {
    const prevColumns = get().columns;
    const prevBoard = get().board;

    // Optimistic update
    set((state) => ({
      columns: state.columns.map((c) =>
        c.id === id ? { ...c, ...updates } : c
      ),
      board: state.board ? {
        ...state.board,
        columns: state.board.columns.map((c) =>
          c.id === id ? { ...c, ...updates } : c
        ),
      } : null,
    }));

    try {
      await api.columns.updateColumn(id, updates);
    } catch (error) {
      // Rollback on error
      const errorMessage = error instanceof Error ? error.message : String(error);
      set({
        columns: prevColumns,
        board: prevBoard,
        error: errorMessage,
      });
      toast.error(`Failed to update column: ${errorMessage}`);
      throw error;
    }
  },

  deleteColumn: async (id) => {
    const prevColumns = get().columns;
    const prevBoard = get().board;
    const prevTickets = get().tickets;

    // Optimistic update
    set((state) => {
      const newTickets = { ...state.tickets };
      delete newTickets[id];
      return {
        columns: state.columns.filter((c) => c.id !== id),
        board: state.board ? {
          ...state.board,
          columns: state.board.columns.filter((c) => c.id !== id),
        } : null,
        tickets: newTickets,
      };
    });

    try {
      await api.columns.deleteColumn(id);
      toast.success('Column deleted');
    } catch (error) {
      // Rollback on error
      const errorMessage = error instanceof Error ? error.message : String(error);
      set({
        columns: prevColumns,
        board: prevBoard,
        tickets: prevTickets,
        error: errorMessage,
      });
      toast.error(`Failed to delete column: ${errorMessage}`);
      throw error;
    }
  },

  reorderColumns: async (columnIds) => {
    const prevColumns = get().columns;

    // Optimistic update
    set((state) => {
      const newColumns = columnIds.map((id, index) => {
        const column = state.columns.find((c) => c.id === id)!;
        return { ...column, position: index };
      });
      return {
        columns: newColumns,
        board: state.board ? { ...state.board, columns: newColumns } : null,
      };
    });

    try {
      await api.columns.reorderColumns(columnIds);
    } catch (error) {
      // Rollback on error
      const errorMessage = error instanceof Error ? error.message : String(error);
      set({
        columns: prevColumns,
        error: errorMessage,
      });
      toast.error(`Failed to reorder columns: ${errorMessage}`);
      throw error;
    }
  },

  // ===========================================
  // TICKETS
  // ===========================================

  setTickets: (columnId, tickets) => {
    set((state) => ({
      tickets: { ...state.tickets, [columnId]: tickets },
    }));
  },

  addTicket: async (ticketData) => {
    try {
      // Call backend - it generates ID and timestamps
      const newTicket = await api.tickets.createTicket(ticketData);

      set((state) => ({
        tickets: {
          ...state.tickets,
          [ticketData.columnId]: [...(state.tickets[ticketData.columnId] || []), newTicket],
        },
      }));

      return newTicket;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      set({ error: errorMessage });
      toast.error(`Failed to create ticket: ${errorMessage}`);
      throw error;
    }
  },

  updateTicket: async (id, updates) => {
    const prevTickets = get().tickets;

    // Find current ticket to get columnId
    let ticketColumnId: string | undefined;
    for (const [columnId, columnTickets] of Object.entries(get().tickets)) {
      if (columnTickets.some(t => t.id === id)) {
        ticketColumnId = columnId;
        break;
      }
    }

    if (!ticketColumnId) {
      throw new Error(`Ticket ${id} not found`);
    }

    // Optimistic update
    set((state) => {
      const newTickets = { ...state.tickets };
      for (const columnId of Object.keys(newTickets)) {
        newTickets[columnId] = newTickets[columnId].map((t) => {
          if (t.id !== id) return t;

          // Handle labels conversion if needed
          const { labels: labelIds, dueDate, ...rest } = updates;
          const updatedLabels = labelIds
            ? state.labels.filter((l) => labelIds.includes(l.id))
            : t.labels;

          // Handle dueDate - convert null to undefined
          const updatedDueDate = dueDate === null ? undefined : (dueDate ?? t.dueDate);

          return {
            ...t,
            ...rest,
            labels: updatedLabels,
            dueDate: updatedDueDate,
          };
        });
      }
      return { tickets: newTickets };
    });

    try {
      // Call backend
      const updatedTicket = await api.tickets.updateTicket(id, updates);

      // Sync with backend response
      set((state) => {
        const newTickets = { ...state.tickets };
        for (const columnId of Object.keys(newTickets)) {
          newTickets[columnId] = newTickets[columnId].map((t) =>
            t.id === id ? updatedTicket : t
          );
        }
        return { tickets: newTickets };
      });
    } catch (error) {
      // Rollback on error
      const errorMessage = error instanceof Error ? error.message : String(error);
      set({
        tickets: prevTickets,
        error: errorMessage,
      });
      toast.error(`Failed to update ticket: ${errorMessage}`);
      throw error;
    }
  },

  deleteTicket: async (id) => {
    const prevTickets = get().tickets;

    // Optimistic update
    set((state) => {
      const newTickets = { ...state.tickets };
      for (const columnId of Object.keys(newTickets)) {
        newTickets[columnId] = newTickets[columnId].filter((t) => t.id !== id);
      }
      return { tickets: newTickets };
    });

    try {
      await api.tickets.deleteTicket(id);
      toast.success('Ticket deleted');
    } catch (error) {
      // Rollback on error
      const errorMessage = error instanceof Error ? error.message : String(error);
      set({
        tickets: prevTickets,
        error: errorMessage,
      });
      toast.error(`Failed to delete ticket: ${errorMessage}`);
      throw error;
    }
  },

  moveTicket: async ({ ticketId, targetColumnId, position }) => {
    const prevTickets = get().tickets;

    // Optimistic update
    set((state) => {
      const newTickets = { ...state.tickets };
      let movedTicket: Ticket | undefined;

      // Find and remove ticket from source column
      for (const columnId of Object.keys(newTickets)) {
        const idx = newTickets[columnId].findIndex((t) => t.id === ticketId);
        if (idx !== -1) {
          [movedTicket] = newTickets[columnId].splice(idx, 1);
          newTickets[columnId] = [...newTickets[columnId]];
          break;
        }
      }

      if (movedTicket) {
        // Add to target column
        movedTicket = {
          ...movedTicket,
          columnId: targetColumnId,
          position,
        };

        const targetTickets = [...(newTickets[targetColumnId] || [])];
        targetTickets.splice(position, 0, movedTicket);
        newTickets[targetColumnId] = targetTickets;
      }

      return { tickets: newTickets };
    });

    try {
      await api.tickets.moveTicket(ticketId, targetColumnId, position);
    } catch (error) {
      // Rollback on error
      const errorMessage = error instanceof Error ? error.message : String(error);
      set({
        tickets: prevTickets,
        error: errorMessage,
      });
      toast.error('Failed to move ticket. Changes reverted.');
      throw error;
    }
  },

  // ===========================================
  // LABELS
  // ===========================================

  setLabels: (labels) => {
    set({ labels });
  },

  addLabel: async (name, color) => {
    try {
      const newLabel = await api.labels.createLabel({ name, color });

      set((state) => ({
        labels: [...state.labels, newLabel],
      }));

      return newLabel;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      set({ error: errorMessage });
      toast.error(`Failed to create label: ${errorMessage}`);
      throw error;
    }
  },

  deleteLabel: async (id) => {
    const prevLabels = get().labels;
    const prevTickets = get().tickets;

    // Optimistic update
    set((state) => {
      const newTickets = { ...state.tickets };
      for (const columnId of Object.keys(newTickets)) {
        newTickets[columnId] = newTickets[columnId].map((t) => ({
          ...t,
          labels: t.labels.filter((l) => l.id !== id),
        }));
      }
      return {
        labels: state.labels.filter((l) => l.id !== id),
        tickets: newTickets,
      };
    });

    try {
      await api.labels.deleteLabel(id);
      toast.success('Label deleted');
    } catch (error) {
      // Rollback on error
      const errorMessage = error instanceof Error ? error.message : String(error);
      set({
        labels: prevLabels,
        tickets: prevTickets,
        error: errorMessage,
      });
      toast.error(`Failed to delete label: ${errorMessage}`);
      throw error;
    }
  },

  // ===========================================
  // LOAD
  // ===========================================

  loadBoard: async () => {
    set({ isLoading: true, error: null });

    try {
      // Initialize default board
      const boardId = await api.board.getDefaultBoard();

      // Load all data in parallel
      const [columns, labels, tickets] = await Promise.all([
        api.columns.getColumns(),
        api.labels.getLabels(),
        api.tickets.getTickets(),
      ]);

      // Group tickets by column
      const ticketsByColumn: Record<string, Ticket[]> = {};
      for (const column of columns) {
        ticketsByColumn[column.id] = [];
      }
      for (const ticket of tickets) {
        if (!ticketsByColumn[ticket.columnId]) {
          ticketsByColumn[ticket.columnId] = [];
        }
        ticketsByColumn[ticket.columnId].push(ticket);
      }

      // Sort tickets by position within each column
      for (const columnId of Object.keys(ticketsByColumn)) {
        ticketsByColumn[columnId].sort((a, b) => a.position - b.position);
      }

      set({
        columns,
        labels,
        tickets: ticketsByColumn,
        board: {
          id: boardId,
          name: 'Kanban AI',
          columns,
        },
        isLoading: false,
      });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      set({
        error: errorMessage,
        isLoading: false,
      });
      toast.error(`Failed to load board: ${errorMessage}`);
    }
  },
}));

// ===========================================
// SELECTORS
// ===========================================

export const selectTicketsByColumn = (columnId: string) => (state: BoardState) =>
  (state.tickets[columnId] || []).sort((a, b) => a.position - b.position);

export const selectTicketById = (id: string) => (state: BoardState) => {
  for (const tickets of Object.values(state.tickets)) {
    const ticket = tickets.find((t) => t.id === id);
    if (ticket) return ticket;
  }
  return undefined;
};

export const selectColumnById = (id: string) => (state: BoardState) =>
  state.columns.find((c) => c.id === id);
