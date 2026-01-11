// lib/export-import.ts - Export/Import utilities for board data
import type { Ticket, Column, Label, BoardListItem } from '@/types';

// ===========================================
// EXPORT DATA TYPES
// ===========================================

export interface ExportData {
  version: string;
  exportedAt: string;
  boards: ExportBoard[];
}

export interface ExportBoard {
  id: string;
  name: string;
  description?: string;
  columns: Column[];
  labels: Label[];
  tickets: Ticket[];
}

// ===========================================
// VALIDATION
// ===========================================

export interface ValidationResult {
  valid: boolean;
  errors: string[];
  data?: ExportData;
}

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function isArray(value: unknown): value is unknown[] {
  return Array.isArray(value);
}

function hasString(obj: Record<string, unknown>, key: string): boolean {
  return typeof obj[key] === 'string' && obj[key] !== '';
}

function hasNumber(obj: Record<string, unknown>, key: string): boolean {
  return typeof obj[key] === 'number';
}

function validateColumn(col: unknown, index: number): string[] {
  const errors: string[] = [];
  if (!isObject(col)) {
    errors.push(`Column ${index}: Invalid column object`);
    return errors;
  }
  if (!hasString(col, 'id')) errors.push(`Column ${index}: Missing id`);
  if (!hasString(col, 'name')) errors.push(`Column ${index}: Missing name`);
  if (!hasNumber(col, 'position')) errors.push(`Column ${index}: Missing position`);
  return errors;
}

function validateLabel(label: unknown, index: number): string[] {
  const errors: string[] = [];
  if (!isObject(label)) {
    errors.push(`Label ${index}: Invalid label object`);
    return errors;
  }
  if (!hasString(label, 'id')) errors.push(`Label ${index}: Missing id`);
  if (!hasString(label, 'name')) errors.push(`Label ${index}: Missing name`);
  if (!hasString(label, 'color')) errors.push(`Label ${index}: Missing color`);
  return errors;
}

function validateTicket(ticket: unknown, index: number): string[] {
  const errors: string[] = [];
  if (!isObject(ticket)) {
    errors.push(`Ticket ${index}: Invalid ticket object`);
    return errors;
  }
  if (!hasString(ticket, 'id')) errors.push(`Ticket ${index}: Missing id`);
  if (!hasString(ticket, 'title')) errors.push(`Ticket ${index}: Missing title`);
  if (!hasString(ticket, 'columnId')) errors.push(`Ticket ${index}: Missing columnId`);
  if (!hasNumber(ticket, 'position')) errors.push(`Ticket ${index}: Missing position`);
  if (!isArray(ticket.labels)) errors.push(`Ticket ${index}: Missing labels array`);
  if (!isArray(ticket.comments)) errors.push(`Ticket ${index}: Missing comments array`);
  return errors;
}

function validateBoard(board: unknown, index: number): string[] {
  const errors: string[] = [];
  if (!isObject(board)) {
    errors.push(`Board ${index}: Invalid board object`);
    return errors;
  }
  if (!hasString(board, 'id')) errors.push(`Board ${index}: Missing id`);
  if (!hasString(board, 'name')) errors.push(`Board ${index}: Missing name`);

  // Validate columns
  if (!isArray(board.columns)) {
    errors.push(`Board ${index}: Missing columns array`);
  } else {
    board.columns.forEach((col, colIndex) => {
      errors.push(...validateColumn(col, colIndex));
    });
  }

  // Validate labels
  if (!isArray(board.labels)) {
    errors.push(`Board ${index}: Missing labels array`);
  } else {
    board.labels.forEach((label, labelIndex) => {
      errors.push(...validateLabel(label, labelIndex));
    });
  }

  // Validate tickets
  if (!isArray(board.tickets)) {
    errors.push(`Board ${index}: Missing tickets array`);
  } else {
    board.tickets.forEach((ticket, ticketIndex) => {
      errors.push(...validateTicket(ticket, ticketIndex));
    });
  }

  return errors;
}

export function validateImportData(json: unknown): ValidationResult {
  const errors: string[] = [];

  // Check root object
  if (!isObject(json)) {
    return { valid: false, errors: ['Invalid JSON: Expected object'] };
  }

  // Check version
  if (!hasString(json, 'version')) {
    errors.push('Missing version field');
  }

  // Check exportedAt
  if (!hasString(json, 'exportedAt')) {
    errors.push('Missing exportedAt field');
  }

  // Check boards array
  if (!isArray(json.boards)) {
    errors.push('Missing boards array');
  } else {
    json.boards.forEach((board, index) => {
      errors.push(...validateBoard(board, index));
    });
  }

  if (errors.length > 0) {
    return { valid: false, errors };
  }

  return { valid: true, errors: [], data: json as unknown as ExportData };
}

// ===========================================
// EXPORT HELPERS
// ===========================================

export interface ExportInput {
  boards: BoardListItem[];
  columns: Column[];
  labels: Label[];
  tickets: Record<string, Ticket[]>;
  currentBoardId: string | null;
  boardName?: string;
}

export function createExportData(input: ExportInput): ExportData {
  const { boards, columns, labels, tickets, currentBoardId, boardName } = input;

  // Flatten tickets from Record to array
  const allTickets: Ticket[] = [];
  for (const columnTickets of Object.values(tickets)) {
    allTickets.push(...columnTickets);
  }

  // Create single board export for current board
  const exportBoard: ExportBoard = {
    id: currentBoardId || 'default',
    name: boardName || boards.find(b => b.id === currentBoardId)?.name || 'Exported Board',
    columns,
    labels,
    tickets: allTickets,
  };

  return {
    version: '1.0',
    exportedAt: new Date().toISOString(),
    boards: [exportBoard],
  };
}

export function downloadJson(data: ExportData, filename: string): void {
  const json = JSON.stringify(data, null, 2);
  const blob = new Blob([json], { type: 'application/json' });
  const url = URL.createObjectURL(blob);

  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

// ===========================================
// IMPORT HELPERS
// ===========================================

export interface ImportStats {
  boardCount: number;
  columnCount: number;
  labelCount: number;
  ticketCount: number;
}

export function getImportStats(data: ExportData): ImportStats {
  let columnCount = 0;
  let labelCount = 0;
  let ticketCount = 0;

  for (const board of data.boards) {
    columnCount += board.columns.length;
    labelCount += board.labels.length;
    ticketCount += board.tickets.length;
  }

  return {
    boardCount: data.boards.length,
    columnCount,
    labelCount,
    ticketCount,
  };
}

export function readFile(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result as string);
    reader.onerror = () => reject(new Error('Failed to read file'));
    reader.readAsText(file);
  });
}
