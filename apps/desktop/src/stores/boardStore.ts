import { create } from 'zustand';
import type { Ticket, Column, Label, TicketCreate, TicketUpdate, ColumnCreate } from '@/types';

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
  reorderColumns: (columnIds: string[]) => void;

  // Actions - Tickets
  setTickets: (columnId: string, tickets: Ticket[]) => void;
  addTicket: (ticket: TicketCreate) => Promise<Ticket>;
  updateTicket: (id: string, updates: TicketUpdate) => Promise<void>;
  deleteTicket: (id: string) => Promise<void>;
  moveTicket: (params: { ticketId: string; targetColumnId: string; position: number }) => void;

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
    const newColumn: Column = {
      id: crypto.randomUUID(),
      name: column.name,
      position: get().columns.length,
      color: column.color,
      wipLimit: column.wipLimit,
    };

    set((state) => ({
      columns: [...state.columns, newColumn],
      board: state.board ? {
        ...state.board,
        columns: [...state.board.columns, newColumn],
      } : null,
      tickets: { ...state.tickets, [newColumn.id]: [] },
    }));
  },

  updateColumn: async (id, updates) => {
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
  },

  deleteColumn: async (id) => {
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
  },

  reorderColumns: (columnIds) => {
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
    const columnTickets = get().tickets[ticketData.columnId] || [];

    const newTicket: Ticket = {
      id: crypto.randomUUID(),
      title: ticketData.title,
      description: ticketData.description,
      priority: ticketData.priority,
      effort: ticketData.effort,
      columnId: ticketData.columnId,
      position: columnTickets.length,
      labels: [],
      comments: [],
      dueDate: ticketData.dueDate,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    set((state) => ({
      tickets: {
        ...state.tickets,
        [ticketData.columnId]: [...(state.tickets[ticketData.columnId] || []), newTicket],
      },
    }));

    return newTicket;
  },

  updateTicket: async (id, updates) => {
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
            updatedAt: new Date().toISOString(),
          };
        });
      }
      return { tickets: newTickets };
    });
  },

  deleteTicket: async (id) => {
    set((state) => {
      const newTickets = { ...state.tickets };
      for (const columnId of Object.keys(newTickets)) {
        newTickets[columnId] = newTickets[columnId].filter((t) => t.id !== id);
      }
      return { tickets: newTickets };
    });
  },

  moveTicket: ({ ticketId, targetColumnId, position }) => {
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
          updatedAt: new Date().toISOString(),
        };

        const targetTickets = [...(newTickets[targetColumnId] || [])];
        targetTickets.splice(position, 0, movedTicket);
        newTickets[targetColumnId] = targetTickets;
      }

      return { tickets: newTickets };
    });
  },

  // ===========================================
  // LABELS
  // ===========================================

  setLabels: (labels) => {
    set({ labels });
  },

  addLabel: async (name, color) => {
    const newLabel: Label = {
      id: crypto.randomUUID(),
      name,
      color,
    };

    set((state) => ({
      labels: [...state.labels, newLabel],
    }));

    return newLabel;
  },

  deleteLabel: async (id) => {
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
  },

  // ===========================================
  // LOAD
  // ===========================================

  loadBoard: async () => {
    set({ isLoading: true, error: null });

    try {
      // Demo data for now
      const columns: Column[] = [
        { id: '1', name: 'Backlog', position: 0, color: '#71717a' },
        { id: '2', name: 'To Do', position: 1, color: '#3b82f6' },
        { id: '3', name: 'In Progress', position: 2, color: '#eab308' },
        { id: '4', name: 'Review', position: 3, color: '#a855f7' },
        { id: '5', name: 'Done', position: 4, color: '#22c55e' },
      ];

      const labels: Label[] = [
        { id: 'l1', name: 'bug', color: '#ef4444' },
        { id: 'l2', name: 'feature', color: '#6366f1' },
        { id: 'l3', name: 'improvement', color: '#22c55e' },
        { id: 'l4', name: 'ui', color: '#f97316' },
        { id: 'l5', name: 'backend', color: '#a855f7' },
      ];

      // Demo tickets
      const demoTickets: Record<string, Ticket[]> = {
        '1': [
          {
            id: 't1',
            title: 'Research AI providers',
            description: 'Compare Claude, GPT-4, and local models',
            priority: 'medium',
            effort: 'm',
            columnId: '1',
            position: 0,
            labels: [labels[1]],
            comments: [],
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
          },
        ],
        '2': [
          {
            id: 't2',
            title: 'Setup Tauri backend',
            description: 'Initialize Rust backend with SQLite',
            priority: 'high',
            effort: 'l',
            columnId: '2',
            position: 0,
            labels: [labels[4]],
            comments: [],
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
          },
        ],
        '3': [
          {
            id: 't3',
            title: 'Build KanbanBoard component',
            priority: 'critical',
            effort: 'm',
            columnId: '3',
            position: 0,
            labels: [labels[1], labels[3]],
            comments: [],
            dueDate: new Date(Date.now() + 86400000).toISOString(),
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
          },
        ],
        '4': [],
        '5': [],
      };

      set({
        columns,
        labels,
        tickets: demoTickets,
        board: {
          id: 'default',
          name: 'Kanban AI',
          columns,
        },
        isLoading: false,
      });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to load board',
        isLoading: false,
      });
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
