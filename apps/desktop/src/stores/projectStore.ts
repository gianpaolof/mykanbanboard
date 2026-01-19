import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import type { ProjectContext, ProjectContextUpdate } from '@/types';
import { projectContextApi, AgentProjectContext, AgentBoardContext } from '@/lib/tauri';

interface ProjectState {
  // Current board's project context
  context: ProjectContext | null;
  isLoading: boolean;
  error: string | null;

  // Wizard state (per-board tracking)
  wizardCompletedBoards: string[];
  showWizard: boolean;

  // Actions
  loadContext: (boardId: string) => Promise<void>;
  updateContext: (boardId: string, updates: ProjectContextUpdate) => Promise<void>;
  setContext: (boardId: string, context: ProjectContext) => Promise<void>;
  clearContext: (boardId: string) => Promise<void>;
  resetState: () => void;

  // Wizard actions
  markWizardCompleted: (boardId: string) => void;
  isWizardCompleted: (boardId: string) => boolean;
  openWizard: () => void;
  closeWizard: () => void;

  // Helpers for AI calls
  getAgentProjectContext: () => AgentProjectContext | undefined;
  getAgentBoardContext: (boardId: string, boardName: string, columns: Array<{ id: string; name: string }>, labels: string[], totalTickets: number) => AgentBoardContext;
}

const DEFAULT_CONTEXT: ProjectContext = {
  techStack: [],
  conventions: undefined,
  priorityRules: undefined,
  architecture: undefined,
  description: undefined,
  defaultLabels: [],
};

export const useProjectStore = create<ProjectState>()(
  persist(
    (set, get) => ({
      context: null,
      isLoading: false,
      error: null,
      wizardCompletedBoards: [],
      showWizard: false,

      loadContext: async (boardId: string) => {
        set({ isLoading: true, error: null });
        try {
          const context = await projectContextApi.getProjectContext(boardId);
          set({ context, isLoading: false });
        } catch (error) {
          console.error('Failed to load project context:', error);
          set({
            error: error instanceof Error ? error.message : 'Failed to load project context',
            isLoading: false
          });
        }
      },

      updateContext: async (boardId: string, updates: ProjectContextUpdate) => {
        set({ isLoading: true, error: null });
        try {
          const context = await projectContextApi.updateProjectContext(boardId, updates);
          set({ context, isLoading: false });
        } catch (error) {
          console.error('Failed to update project context:', error);
          set({
            error: error instanceof Error ? error.message : 'Failed to update project context',
            isLoading: false
          });
          throw error;
        }
      },

      setContext: async (boardId: string, context: ProjectContext) => {
        set({ isLoading: true, error: null });
        try {
          const savedContext = await projectContextApi.setProjectContext(boardId, context);
          set({ context: savedContext, isLoading: false });
        } catch (error) {
          console.error('Failed to set project context:', error);
          set({
            error: error instanceof Error ? error.message : 'Failed to set project context',
            isLoading: false
          });
          throw error;
        }
      },

      clearContext: async (boardId: string) => {
        set({ isLoading: true, error: null });
        try {
          await projectContextApi.deleteProjectContext(boardId);
          set({ context: null, isLoading: false });
        } catch (error) {
          console.error('Failed to clear project context:', error);
          set({
            error: error instanceof Error ? error.message : 'Failed to clear project context',
            isLoading: false
          });
          throw error;
        }
      },

      resetState: () => {
        set({ context: null, isLoading: false, error: null });
      },

      // Wizard actions
      markWizardCompleted: (boardId: string) => {
        const { wizardCompletedBoards } = get();
        if (!wizardCompletedBoards.includes(boardId)) {
          set({ wizardCompletedBoards: [...wizardCompletedBoards, boardId] });
        }
        set({ showWizard: false });
      },

      isWizardCompleted: (boardId: string) => {
        return get().wizardCompletedBoards.includes(boardId);
      },

      openWizard: () => {
        set({ showWizard: true });
      },

      closeWizard: () => {
        set({ showWizard: false });
      },

      getAgentProjectContext: () => {
        const { context } = get();
        if (!context) return undefined;

        return {
          techStack: context.techStack,
          conventions: context.conventions,
          priorityRules: context.priorityRules,
          architecture: context.architecture,
        };
      },

      getAgentBoardContext: (
        boardId: string,
        boardName: string,
        columns: Array<{ id: string; name: string }>,
        labels: string[],
        totalTickets: number
      ): AgentBoardContext => {
        return {
          boardId,
          boardName,
          columns,
          labels,
          totalTickets,
        };
      },
    }),
    {
      name: 'project-context-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        context: state.context,
        wizardCompletedBoards: state.wizardCompletedBoards,
      }),
    }
  )
);

// Export default context for use in components
export { DEFAULT_CONTEXT };
