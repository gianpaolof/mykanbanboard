/**
 * Tauri API Wrapper
 * Provides type-safe access to Tauri backend commands
 */
import { invoke } from '@tauri-apps/api/core';
import type {
  Ticket,
  TicketCreate,
  TicketUpdate,
  Column,
  ColumnCreate,
  Label,
  LabelCreate,
} from '@/types';

// ===========================================
// BOARD API
// ===========================================

export const boardApi = {
  /**
   * Get or create the default board
   * @returns Board ID
   */
  getDefaultBoard: () => invoke<string>('get_default_board'),
};

// ===========================================
// COLUMN API
// ===========================================

export const columnApi = {
  /**
   * Get all columns ordered by position
   */
  getColumns: () => invoke<Column[]>('get_columns'),

  /**
   * Create a new column
   */
  createColumn: (column: ColumnCreate) =>
    invoke<Column>('create_column', { column }),

  /**
   * Update a column
   */
  updateColumn: (id: string, updates: Partial<Column>) =>
    invoke<Column>('update_column', { id, updates }),

  /**
   * Delete a column (must be empty)
   */
  deleteColumn: (id: string) => invoke<void>('delete_column', { id }),

  /**
   * Reorder columns by providing new order of IDs
   */
  reorderColumns: (columnIds: string[]) =>
    invoke<void>('reorder_columns', { columnIds }),
};

// ===========================================
// TICKET API
// ===========================================

export const ticketApi = {
  /**
   * Get all tickets, optionally filtered by column
   */
  getTickets: (columnId?: string) =>
    invoke<Ticket[]>('get_tickets', { columnId: columnId ?? null }),

  /**
   * Get a single ticket by ID
   */
  getTicket: (id: string) => invoke<Ticket>('get_ticket', { id }),

  /**
   * Create a new ticket
   */
  createTicket: (ticket: TicketCreate) =>
    invoke<Ticket>('create_ticket', { ticket }),

  /**
   * Update a ticket
   */
  updateTicket: (id: string, updates: TicketUpdate) =>
    invoke<Ticket>('update_ticket', { id, updates }),

  /**
   * Delete a ticket
   */
  deleteTicket: (id: string) => invoke<void>('delete_ticket', { id }),

  /**
   * Move a ticket to a different column/position
   */
  moveTicket: (id: string, columnId: string, position: number) =>
    invoke<Ticket>('move_ticket', { id, columnId, position }),
};

// ===========================================
// LABEL API
// ===========================================

export const labelApi = {
  /**
   * Get all labels
   */
  getLabels: () => invoke<Label[]>('get_labels'),

  /**
   * Create a new label
   */
  createLabel: (label: LabelCreate) =>
    invoke<Label>('create_label', { label }),

  /**
   * Update a label
   */
  updateLabel: (id: string, updates: Partial<Label>) =>
    invoke<Label>('update_label', { id, updates }),

  /**
   * Delete a label
   */
  deleteLabel: (id: string) => invoke<void>('delete_label', { id }),

  /**
   * Add a label to a ticket
   */
  addLabelToTicket: (ticketId: string, labelId: string) =>
    invoke<void>('add_label_to_ticket', { ticketId, labelId }),

  /**
   * Remove a label from a ticket
   */
  removeLabelFromTicket: (ticketId: string, labelId: string) =>
    invoke<void>('remove_label_from_ticket', { ticketId, labelId }),
};

// ===========================================
// AGENT API
// ===========================================

export interface AgentTriageResult {
  priority?: string;
  effort?: string;
  labels?: string[];
  reasoning: string;
}

export interface AgentDecomposeResult {
  subtasks: Array<{
    title: string;
    description: string;
    effort?: string;
  }>;
  reasoning: string;
}

export interface AgentChatResult {
  response: string;
  actions?: Array<{
    type: string;
    data: Record<string, unknown>;
  }>;
}

export interface AgentSearchResult {
  results: Array<{
    ticket_id: string;
    title: string;
    description: string;
    score: number;
  }>;
}

export interface AgentDailySummaryResult {
  summary: string;
  stats: {
    total: number;
    by_priority: Record<string, number>;
    by_status: Record<string, number>;
  };
  focus_today: string[];
}

export const agentApi = {
  /**
   * Auto-triage a ticket: assign priority, labels, and effort estimate
   */
  triage: (ticketId: string, title: string, description: string) =>
    invoke<AgentTriageResult>('agent_triage', {
      ticketId,
      title,
      description,
    }),

  /**
   * Decompose a complex task into subtasks
   */
  decompose: (ticketId: string, title: string, description: string) =>
    invoke<AgentDecomposeResult>('agent_decompose', {
      ticketId,
      title,
      description,
    }),

  /**
   * Chat with the AI agent
   */
  chat: (message: string, context?: Record<string, unknown>) =>
    invoke<AgentChatResult>('agent_chat', {
      message,
      context: context ?? null,
    }),

  /**
   * Generate daily summary of tickets
   */
  dailySummary: () =>
    invoke<AgentDailySummaryResult>('agent_daily_summary'),

  /**
   * Semantic search for tickets
   */
  search: (query: string, limit?: number) =>
    invoke<AgentSearchResult>('agent_search', {
      query,
      limit: limit ?? null,
    }),

  /**
   * Check if agent is available and healthy
   */
  health: () => invoke<boolean>('agent_health'),
};

// ===========================================
// UNIFIED API
// ===========================================

export const api = {
  board: boardApi,
  columns: columnApi,
  tickets: ticketApi,
  labels: labelApi,
  agent: agentApi,
};

export default api;
