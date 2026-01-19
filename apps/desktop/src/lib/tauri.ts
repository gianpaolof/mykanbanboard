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
  Board,
  BoardListItem,
  BoardCreate,
  BoardUpdate,
  Subtask,
  SubtaskCreate,
  SubtaskUpdate,
  AutomationRule,
  AutomationRuleCreate,
  AutomationRuleUpdate,
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

  /**
   * Get all boards (lightweight list)
   */
  getBoards: () => invoke<BoardListItem[]>('get_boards'),

  /**
   * Get a single board by ID
   */
  getBoard: (id: string) => invoke<Board>('get_board', { id }),

  /**
   * Create a new board
   */
  createBoard: (board: BoardCreate) => invoke<Board>('create_board', { board }),

  /**
   * Update a board
   */
  updateBoard: (id: string, updates: BoardUpdate) =>
    invoke<Board>('update_board', { id, updates }),

  /**
   * Delete a board
   */
  deleteBoard: (id: string) => invoke<void>('delete_board', { id }),
};

// ===========================================
// COLUMN API
// ===========================================

export const columnApi = {
  /**
   * Get columns, optionally filtered by board
   */
  getColumns: (boardId?: string) =>
    invoke<Column[]>('get_columns', { boardId: boardId ?? null }),

  /**
   * Create a new column
   */
  createColumn: (column: ColumnCreate, boardId?: string) =>
    invoke<Column>('create_column', { boardId: boardId ?? null, column }),

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
   * Get all tickets, optionally filtered by board and/or column
   */
  getTickets: (boardId?: string, columnId?: string) =>
    invoke<Ticket[]>('get_tickets', { boardId: boardId ?? null, columnId: columnId ?? null }),

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
// SUBTASK API
// ===========================================

export const subtaskApi = {
  /**
   * Get all subtasks for a ticket
   */
  getSubtasks: (parentTicketId: string) =>
    invoke<Subtask[]>('get_subtasks', { parentTicketId }),

  /**
   * Create a new subtask
   */
  createSubtask: (subtask: SubtaskCreate) =>
    invoke<Subtask>('create_subtask', { subtask }),

  /**
   * Update a subtask
   */
  updateSubtask: (id: string, updates: SubtaskUpdate) =>
    invoke<Subtask>('update_subtask', { id, updates }),

  /**
   * Delete a subtask
   */
  deleteSubtask: (id: string) => invoke<void>('delete_subtask', { id }),

  /**
   * Toggle subtask completion status
   */
  toggleSubtask: (id: string) => invoke<Subtask>('toggle_subtask', { id }),

  /**
   * Reorder subtasks by providing new order of IDs
   */
  reorderSubtasks: (subtaskIds: string[]) =>
    invoke<void>('reorder_subtasks', { subtaskIds }),
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
  action?: string;
  params?: Record<string, unknown>;
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
  greeting: string;
  focus_today: string[];
  blockers: string[];
  quick_wins: string[];
}

export interface DailySummaryTicket {
  id: string;
  title: string;
  description?: string;
  status?: string;
  priority?: string;
  labels?: string[];
  due_date?: string;
  column_id?: string;
}

export interface DailySummaryRequest {
  in_progress: DailySummaryTicket[];
  blocked: DailySummaryTicket[];
  due_soon: DailySummaryTicket[];
  recently_completed: DailySummaryTicket[];
}

export interface SyncTicketsRequest {
  tickets: DailySummaryTicket[];
  force_full_sync?: boolean;
}

export interface SyncStatus {
  success: boolean;
  synced_count: number;
  total_count: number;
  last_sync: string | null;
}

export interface CacheStats {
  entries: number;
  max_entries: number;
  hits: number;
  misses: number;
  evictions: number;
  hit_rate: number;
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
   * Now requires actual ticket data for meaningful summaries
   */
  dailySummary: (request: DailySummaryRequest) =>
    invoke<AgentDailySummaryResult>('agent_daily_summary', { request }),

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

  /**
   * Sync tickets to ChromaDB for semantic search
   * Call this on app startup or when tickets change
   */
  syncTickets: (request: SyncTicketsRequest) =>
    invoke<SyncStatus>('agent_sync_tickets', { request }),

  /**
   * Get ChromaDB sync status
   */
  getSyncStatus: () =>
    invoke<SyncStatus>('agent_sync_status'),

  /**
   * Invalidate context cache
   */
  invalidateCache: (boardId?: string) =>
    invoke<{ invalidated: number | string; board_id?: string }>('agent_invalidate_cache', {
      boardId: boardId ?? null,
    }),

  /**
   * Get cache statistics
   */
  getCacheStats: () =>
    invoke<CacheStats>('agent_cache_stats'),
};

// ===========================================
// AUTOMATION RULES API
// ===========================================

export const automationApi = {
  /**
   * Get all automation rules for a board
   */
  getRules: (boardId: string) =>
    invoke<AutomationRule[]>('get_automation_rules', { boardId }),

  /**
   * Get a single automation rule by ID
   */
  getRule: (id: string) =>
    invoke<AutomationRule>('get_automation_rule', { id }),

  /**
   * Create a new automation rule
   */
  createRule: (rule: AutomationRuleCreate) =>
    invoke<AutomationRule>('create_automation_rule', { rule }),

  /**
   * Update an automation rule
   */
  updateRule: (id: string, updates: AutomationRuleUpdate) =>
    invoke<AutomationRule>('update_automation_rule', { id, updates }),

  /**
   * Delete an automation rule
   */
  deleteRule: (id: string) => invoke<void>('delete_automation_rule', { id }),

  /**
   * Toggle an automation rule on/off
   */
  toggleRule: (id: string) =>
    invoke<AutomationRule>('toggle_automation_rule', { id }),

  /**
   * Record that an automation rule was triggered
   */
  recordTrigger: (id: string) =>
    invoke<AutomationRule>('record_automation_trigger', { id }),
};

// ===========================================
// UNIFIED API
// ===========================================

export const api = {
  board: boardApi,
  columns: columnApi,
  tickets: ticketApi,
  labels: labelApi,
  subtasks: subtaskApi,
  agent: agentApi,
  automations: automationApi,
};

export default api;
