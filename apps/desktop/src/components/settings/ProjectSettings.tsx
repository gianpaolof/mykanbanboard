// components/settings/ProjectSettings.tsx - Project context configuration for AI
import { useState, useEffect } from 'react';
import { X, Plus, Sparkles, Code, FileText, Tags, AlertTriangle, Wand2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useProjectStore, DEFAULT_CONTEXT } from '@/stores/projectStore';
import { useBoardStore } from '@/stores/boardStore';
import { SettingsSection } from './SettingsSection';
import type { ProjectContext } from '@/types';

// Common tech stack options
const TECH_STACK_SUGGESTIONS = [
  'React', 'Vue', 'Angular', 'Svelte', 'Next.js', 'Nuxt.js',
  'TypeScript', 'JavaScript', 'Python', 'Rust', 'Go', 'Java',
  'Node.js', 'FastAPI', 'Django', 'Rails', 'Express',
  'PostgreSQL', 'MySQL', 'MongoDB', 'SQLite', 'Redis',
  'Docker', 'Kubernetes', 'AWS', 'GCP', 'Azure',
  'GraphQL', 'REST', 'gRPC', 'WebSocket',
  'Tailwind', 'SCSS', 'CSS-in-JS', 'Material UI',
];

export function ProjectSettings() {
  const boardId = useBoardStore((state) => state.currentBoardId);
  const { context, isLoading, error, loadContext, setContext, openWizard } = useProjectStore();

  // Local state for editing
  const [localContext, setLocalContext] = useState<ProjectContext>(
    context || DEFAULT_CONTEXT
  );
  const [newTech, setNewTech] = useState('');
  const [newLabel, setNewLabel] = useState('');
  const [hasChanges, setHasChanges] = useState(false);

  // Load context when board changes
  useEffect(() => {
    if (boardId) {
      loadContext(boardId);
    }
  }, [boardId, loadContext]);

  // Sync local state with loaded context
  useEffect(() => {
    if (context) {
      setLocalContext(context);
      setHasChanges(false);
    }
  }, [context]);

  const handleChange = (updates: Partial<ProjectContext>) => {
    setLocalContext((prev) => ({ ...prev, ...updates }));
    setHasChanges(true);
  };

  const handleAddTech = () => {
    if (newTech.trim() && !localContext.techStack.includes(newTech.trim())) {
      handleChange({ techStack: [...localContext.techStack, newTech.trim()] });
      setNewTech('');
    }
  };

  const handleRemoveTech = (tech: string) => {
    handleChange({ techStack: localContext.techStack.filter((t) => t !== tech) });
  };

  const handleAddLabel = () => {
    if (newLabel.trim() && !localContext.defaultLabels.includes(newLabel.trim())) {
      handleChange({ defaultLabels: [...localContext.defaultLabels, newLabel.trim()] });
      setNewLabel('');
    }
  };

  const handleRemoveLabel = (label: string) => {
    handleChange({ defaultLabels: localContext.defaultLabels.filter((l) => l !== label) });
  };

  const handleSave = async () => {
    if (!boardId) return;
    try {
      await setContext(boardId, localContext);
      setHasChanges(false);
    } catch (err) {
      console.error('Failed to save project context:', err);
    }
  };

  if (!boardId) {
    return (
      <div className="flex items-center justify-center p-8 text-text-tertiary">
        <AlertTriangle className="w-5 h-5 mr-2" />
        <span>No board selected</span>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header info */}
      <div className="flex items-start gap-3 p-4 rounded-xl bg-gradient-to-r from-indigo-500/10 to-purple-500/10 border border-accent/20">
        <Sparkles className="w-5 h-5 text-accent mt-0.5" />
        <div className="flex-1">
          <h4 className="text-sm font-medium text-text-primary">
            Project Context for AI
          </h4>
          <p className="text-xs text-text-tertiary mt-1">
            Configure project-specific information to help the AI make better decisions
            when triaging tickets, decomposing tasks, and suggesting labels.
          </p>
        </div>
        <button
          onClick={openWizard}
          className={cn(
            'flex items-center gap-2 px-3 py-1.5 rounded-lg',
            'bg-accent/20 text-accent text-sm font-medium',
            'hover:bg-accent/30 transition-colors'
          )}
        >
          <Wand2 className="w-4 h-4" />
          <span>Setup Wizard</span>
        </button>
      </div>

      {error && (
        <div className="flex items-center gap-2 p-3 rounded-lg bg-status-error/10 text-status-error text-sm">
          <AlertTriangle className="w-4 h-4" />
          <span>{error}</span>
        </div>
      )}

      {/* Tech Stack */}
      <SettingsSection
        title="Tech Stack"
        description="Technologies used in your project. AI will consider these for labels and effort estimates."
      >
        <div className="flex flex-wrap gap-2">
          {localContext.techStack.map((tech) => (
            <span
              key={tech}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-accent-muted text-accent text-sm font-medium"
            >
              <Code className="w-3.5 h-3.5" />
              {tech}
              <button
                onClick={() => handleRemoveTech(tech)}
                className="ml-1 hover:text-status-error transition-colors"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </span>
          ))}
        </div>

        <div className="flex gap-2">
          <input
            type="text"
            value={newTech}
            onChange={(e) => setNewTech(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleAddTech()}
            placeholder="Add technology..."
            list="tech-suggestions"
            className={cn(
              'flex-1 px-3 py-2 bg-bg-tertiary border border-border-subtle rounded-lg',
              'text-sm text-text-primary placeholder:text-text-muted',
              'focus:outline-none focus:border-accent focus:ring-2 focus:ring-accent/20'
            )}
          />
          <datalist id="tech-suggestions">
            {TECH_STACK_SUGGESTIONS.filter(
              (t) => !localContext.techStack.includes(t)
            ).map((tech) => (
              <option key={tech} value={tech} />
            ))}
          </datalist>
          <button
            onClick={handleAddTech}
            disabled={!newTech.trim()}
            className={cn(
              'px-3 py-2 rounded-lg bg-accent text-white text-sm font-medium',
              'hover:bg-accent/90 transition-colors',
              'disabled:opacity-50 disabled:cursor-not-allowed'
            )}
          >
            <Plus className="w-4 h-4" />
          </button>
        </div>
      </SettingsSection>

      {/* Project Description */}
      <SettingsSection
        title="Project Description"
        description="Brief description to help AI understand the project context"
      >
        <textarea
          value={localContext.description || ''}
          onChange={(e) => handleChange({ description: e.target.value || undefined })}
          placeholder="e.g., A desktop kanban app with AI-powered ticket management..."
          rows={3}
          className={cn(
            'w-full px-3 py-2 bg-bg-tertiary border border-border-subtle rounded-lg',
            'text-sm text-text-primary placeholder:text-text-muted resize-none',
            'focus:outline-none focus:border-accent focus:ring-2 focus:ring-accent/20'
          )}
        />
      </SettingsSection>

      {/* Architecture */}
      <SettingsSection
        title="Architecture"
        description="Describe your project architecture (monorepo, microservices, etc.)"
      >
        <textarea
          value={localContext.architecture || ''}
          onChange={(e) => handleChange({ architecture: e.target.value || undefined })}
          placeholder="e.g., Monorepo with React frontend, Rust backend (Tauri), Python AI agent..."
          rows={2}
          className={cn(
            'w-full px-3 py-2 bg-bg-tertiary border border-border-subtle rounded-lg',
            'text-sm text-text-primary placeholder:text-text-muted resize-none',
            'focus:outline-none focus:border-accent focus:ring-2 focus:ring-accent/20'
          )}
        />
      </SettingsSection>

      {/* Conventions */}
      <SettingsSection
        title="Conventions"
        description="Coding conventions and patterns the AI should follow"
      >
        <textarea
          value={localContext.conventions || ''}
          onChange={(e) => handleChange({ conventions: e.target.value || undefined })}
          placeholder="e.g., Use kebab-case for files, PascalCase for components, always write tests..."
          rows={2}
          className={cn(
            'w-full px-3 py-2 bg-bg-tertiary border border-border-subtle rounded-lg',
            'text-sm text-text-primary placeholder:text-text-muted resize-none',
            'focus:outline-none focus:border-accent focus:ring-2 focus:ring-accent/20'
          )}
        />
      </SettingsSection>

      {/* Default Labels */}
      <SettingsSection
        title="Default Labels"
        description="Labels the AI can suggest when triaging tickets"
      >
        <div className="flex flex-wrap gap-2">
          {localContext.defaultLabels.map((label) => (
            <span
              key={label}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-bg-elevated border border-border-subtle text-text-secondary text-sm"
            >
              <Tags className="w-3.5 h-3.5" />
              {label}
              <button
                onClick={() => handleRemoveLabel(label)}
                className="ml-1 hover:text-status-error transition-colors"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </span>
          ))}
        </div>

        <div className="flex gap-2">
          <input
            type="text"
            value={newLabel}
            onChange={(e) => setNewLabel(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleAddLabel()}
            placeholder="Add label..."
            className={cn(
              'flex-1 px-3 py-2 bg-bg-tertiary border border-border-subtle rounded-lg',
              'text-sm text-text-primary placeholder:text-text-muted',
              'focus:outline-none focus:border-accent focus:ring-2 focus:ring-accent/20'
            )}
          />
          <button
            onClick={handleAddLabel}
            disabled={!newLabel.trim()}
            className={cn(
              'px-3 py-2 rounded-lg bg-accent text-white text-sm font-medium',
              'hover:bg-accent/90 transition-colors',
              'disabled:opacity-50 disabled:cursor-not-allowed'
            )}
          >
            <Plus className="w-4 h-4" />
          </button>
        </div>
      </SettingsSection>

      {/* Save Button */}
      {hasChanges && (
        <div className="flex justify-end pt-4 border-t border-border-subtle">
          <button
            onClick={handleSave}
            disabled={isLoading}
            className={cn(
              'px-6 py-2.5 rounded-lg bg-accent text-white font-medium',
              'hover:bg-accent/90 transition-colors',
              'disabled:opacity-50 disabled:cursor-not-allowed',
              'flex items-center gap-2'
            )}
          >
            {isLoading ? (
              <>
                <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <FileText className="w-4 h-4" />
                Save Project Context
              </>
            )}
          </button>
        </div>
      )}
    </div>
  );
}
