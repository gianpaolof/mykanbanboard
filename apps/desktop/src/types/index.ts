// Tipi base per Kanban AI

// ===========================================
// TICKET
// ===========================================

export type Priority = 'low' | 'medium' | 'high' | 'critical';
export type Effort = 'xs' | 's' | 'm' | 'l' | 'xl';

export interface Ticket {
  id: string;
  title: string;
  description?: string;
  priority?: Priority;
  effort?: Effort;
  columnId: string;
  position: number;
  labels: Label[];
  dueDate?: string; // ISO date string
  comments: Comment[];
  createdAt: string;
  updatedAt: string;
}

export interface TicketCreate {
  title: string;
  description?: string;
  columnId: string;
  priority?: Priority;
  effort?: Effort;
  labels?: string[]; // label IDs
  dueDate?: string;
}

export interface TicketUpdate {
  title?: string;
  description?: string;
  priority?: Priority;
  effort?: Effort;
  columnId?: string;
  position?: number;
  labels?: string[];
  dueDate?: string | null;
}

// ===========================================
// COLUMN
// ===========================================

export interface Column {
  id: string;
  name: string;
  position: number;
  color?: string;
  wipLimit?: number;
}

export interface ColumnCreate {
  name: string;
  color?: string;
  wipLimit?: number;
}

// ===========================================
// LABEL
// ===========================================

export interface Label {
  id: string;
  name: string;
  color: string;
}

export interface LabelCreate {
  name: string;
  color: string;
}

// ===========================================
// COMMENT
// ===========================================

export interface Comment {
  id: string;
  ticketId: string;
  content: string;
  createdAt: string;
}

// ===========================================
// SUBTASK
// ===========================================

export interface Subtask {
  id: string;
  parentTicketId: string;
  title: string;
  description?: string;
  completed: boolean;
  position: number;
  createdAt: string;
  updatedAt: string;
}

export interface SubtaskCreate {
  parentTicketId: string;
  title: string;
  description?: string;
}

export interface SubtaskUpdate {
  title?: string;
  description?: string;
  completed?: boolean;
  position?: number;
}

// ===========================================
// PROJECT CONTEXT (for AI operations)
// ===========================================

export interface ProjectContext {
  techStack: string[];
  conventions?: string;
  priorityRules?: Record<string, unknown>;
  architecture?: string;
  description?: string;
  defaultLabels: string[];
}

export interface ProjectContextUpdate {
  techStack?: string[];
  conventions?: string;
  priorityRules?: Record<string, unknown>;
  architecture?: string;
  description?: string;
  defaultLabels?: string[];
}

// ===========================================
// BOARD
// ===========================================

export interface Board {
  id: string;
  name: string;
  description?: string;
  projectContext?: ProjectContext;
  columns: Column[];
  createdAt: string;
  updatedAt: string;
}

export interface BoardListItem {
  id: string;
  name: string;
  ticketCount?: number;
  updatedAt: string;
}

export interface BoardCreate {
  name: string;
  description?: string;
}

export interface BoardUpdate {
  name?: string;
  description?: string;
}

// ===========================================
// AI AGENT
// ===========================================

export interface TriageResult {
  priority: Priority;
  labels: string[];
  effort: Effort;
  reasoning: string;
}

export interface DecomposeResult {
  subtasks: {
    title: string;
    description: string;
    effort: Effort;
  }[];
  dependencies: [number, number][]; // [from, to]
}

export interface DailySummary {
  greeting: string;
  focusToday: {
    ticketId: string;
    title: string;
    priority: Priority;
    reason: string;
  }[];
  blockers: string[];
  quickWins: string[];
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  action?: {
    type: string;
    params: Record<string, unknown>;
  };
}

// ===========================================
// UI STATE
// ===========================================

export type ViewMode = 'board' | 'list' | 'timeline' | 'calendar';

export interface ModalState {
  isOpen: boolean;
  ticketId?: string;
}

// ===========================================
// UTILITY TYPES
// ===========================================

export type SortDirection = 'asc' | 'desc';

export interface SortConfig {
  field: keyof Ticket;
  direction: SortDirection;
}

export interface FilterConfig {
  priority?: Priority[];
  labels?: string[];
  search?: string;
  dueBefore?: string;
  dueAfter?: string;
}

// ===========================================
// AUTOMATION RULES
// ===========================================

export type TriggerType =
  | 'ticket_created'
  | 'ticket_moved'
  | 'ticket_updated'
  | 'label_added'
  | 'label_removed'
  | 'due_date_approaching'
  | 'priority_changed';

export type ActionType =
  | 'move_ticket'
  | 'set_priority'
  | 'add_label'
  | 'remove_label'
  | 'set_due_date'
  | 'notify'
  | 'auto_triage';

export interface AutomationRule {
  id: string;
  boardId: string;
  name: string;
  description: string;
  enabled: boolean;
  triggerType: TriggerType;
  triggerConfig: Record<string, unknown>;
  actionType: ActionType;
  actionConfig: Record<string, unknown>;
  lastTriggeredAt?: string;
  triggerCount: number;
  createdAt: string;
  updatedAt: string;
}

export interface AutomationRuleCreate {
  boardId: string;
  name: string;
  description: string;
  triggerType: TriggerType;
  triggerConfig?: Record<string, unknown>;
  actionType: ActionType;
  actionConfig?: Record<string, unknown>;
}

export interface AutomationRuleUpdate {
  name?: string;
  description?: string;
  enabled?: boolean;
  triggerType?: TriggerType;
  triggerConfig?: Record<string, unknown>;
  actionType?: ActionType;
  actionConfig?: Record<string, unknown>;
}

export interface ParsedRule {
  ruleName: string;
  triggerType: TriggerType;
  triggerConfig: Record<string, unknown>;
  actionType: ActionType;
  actionConfig: Record<string, unknown>;
  confidence: number;
  explanation: string;
}
