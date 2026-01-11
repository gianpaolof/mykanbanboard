// types/settings.ts - Settings type definitions

export type AIModel = 'claude-3-5-sonnet' | 'claude-3-opus' | 'gpt-4' | 'gpt-4-turbo';
export type AIProvider = 'anthropic' | 'openai';

export interface AISettings {
  apiKey: string;
  model: AIModel;
  provider: AIProvider;
  baseUrl?: string; // For custom endpoints
}

export interface BoardSettings {
  defaultColumns: string[];
  wipLimits: Record<string, number>;
  autoAssignPriority: boolean;
  enableAITriage: boolean;
}

export interface KeyboardSettings {
  enabled: boolean;
}

export interface Settings {
  ai: AISettings;
  board: BoardSettings;
  keyboard: KeyboardSettings;
}

export const DEFAULT_SETTINGS: Settings = {
  ai: {
    apiKey: '',
    model: 'claude-3-5-sonnet',
    provider: 'anthropic',
  },
  board: {
    defaultColumns: ['To Do', 'In Progress', 'Review', 'Done'],
    wipLimits: {},
    autoAssignPriority: true,
    enableAITriage: true,
  },
  keyboard: {
    enabled: true,
  },
};
