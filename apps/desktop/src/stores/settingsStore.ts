// stores/settingsStore.ts - Settings state management with persistence
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Settings, AIModel, AIProvider } from '@/types/settings';
import { DEFAULT_SETTINGS } from '@/types/settings';

interface SettingsState extends Settings {
  // AI actions
  setAIApiKey: (apiKey: string) => void;
  setAIModel: (model: AIModel) => void;
  setAIProvider: (provider: AIProvider) => void;

  // Board actions
  setWIPLimit: (columnId: string, limit: number) => void;
  removeWIPLimit: (columnId: string) => void;
  setDefaultColumns: (columns: string[]) => void;
  toggleAutoAssignPriority: () => void;
  toggleAITriage: () => void;

  // Keyboard actions
  toggleKeyboardShortcuts: () => void;

  // General actions
  resetSettings: () => void;
}

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      // Initial state from defaults
      ...DEFAULT_SETTINGS,

      // AI actions
      setAIApiKey: (apiKey) =>
        set((state) => ({
          ai: { ...state.ai, apiKey },
        })),

      setAIModel: (model) =>
        set((state) => ({
          ai: { ...state.ai, model },
        })),

      setAIProvider: (provider) =>
        set((state) => ({
          ai: { ...state.ai, provider },
        })),

      // Board actions
      setWIPLimit: (columnId, limit) =>
        set((state) => ({
          board: {
            ...state.board,
            wipLimits: { ...state.board.wipLimits, [columnId]: limit },
          },
        })),

      removeWIPLimit: (columnId) =>
        set((state) => {
          const newLimits = { ...state.board.wipLimits };
          delete newLimits[columnId];
          return {
            board: { ...state.board, wipLimits: newLimits },
          };
        }),

      setDefaultColumns: (columns) =>
        set((state) => ({
          board: { ...state.board, defaultColumns: columns },
        })),

      toggleAutoAssignPriority: () =>
        set((state) => ({
          board: {
            ...state.board,
            autoAssignPriority: !state.board.autoAssignPriority,
          },
        })),

      toggleAITriage: () =>
        set((state) => ({
          board: {
            ...state.board,
            enableAITriage: !state.board.enableAITriage,
          },
        })),

      // Keyboard actions
      toggleKeyboardShortcuts: () =>
        set((state) => ({
          keyboard: {
            ...state.keyboard,
            enabled: !state.keyboard.enabled,
          },
        })),

      // General actions
      resetSettings: () => set(DEFAULT_SETTINGS),
    }),
    {
      name: 'kanban-settings',
    }
  )
);
