// components/settings/ProjectWizard.tsx - First-time project setup wizard
import { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  X,
  ChevronRight,
  ChevronLeft,
  Sparkles,
  Code,
  FileText,
  Tags,
  Plus,
  Check,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useProjectStore, DEFAULT_CONTEXT } from '@/stores/projectStore';
import { useBoardStore } from '@/stores/boardStore';
import type { ProjectContext } from '@/types';

interface ProjectWizardProps {
  open: boolean;
  onClose: () => void;
  onComplete?: () => void;
}

// Common tech stack suggestions
const TECH_STACK_OPTIONS = [
  { label: 'React', category: 'Frontend' },
  { label: 'Vue', category: 'Frontend' },
  { label: 'Angular', category: 'Frontend' },
  { label: 'Svelte', category: 'Frontend' },
  { label: 'Next.js', category: 'Frontend' },
  { label: 'TypeScript', category: 'Language' },
  { label: 'JavaScript', category: 'Language' },
  { label: 'Python', category: 'Language' },
  { label: 'Rust', category: 'Language' },
  { label: 'Go', category: 'Language' },
  { label: 'Node.js', category: 'Backend' },
  { label: 'FastAPI', category: 'Backend' },
  { label: 'Django', category: 'Backend' },
  { label: 'Express', category: 'Backend' },
  { label: 'Rails', category: 'Backend' },
  { label: 'PostgreSQL', category: 'Database' },
  { label: 'MySQL', category: 'Database' },
  { label: 'MongoDB', category: 'Database' },
  { label: 'SQLite', category: 'Database' },
  { label: 'Redis', category: 'Database' },
  { label: 'Docker', category: 'DevOps' },
  { label: 'Kubernetes', category: 'DevOps' },
  { label: 'AWS', category: 'Cloud' },
  { label: 'GCP', category: 'Cloud' },
  { label: 'Azure', category: 'Cloud' },
];

// Common label suggestions
const LABEL_SUGGESTIONS = [
  'bug',
  'feature',
  'enhancement',
  'documentation',
  'refactor',
  'test',
  'performance',
  'security',
  'ui',
  'api',
  'database',
  'infrastructure',
  'frontend',
  'backend',
  'mobile',
  'urgent',
];

const STEPS = [
  { id: 1, title: 'Project Info', icon: FileText },
  { id: 2, title: 'Architecture', icon: Code },
  { id: 3, title: 'Labels', icon: Tags },
];

export function ProjectWizard({ open, onClose, onComplete }: ProjectWizardProps) {
  const boardId = useBoardStore((state) => state.currentBoardId);
  const { setContext, isLoading } = useProjectStore();

  const [step, setStep] = useState(1);
  const [context, setContextState] = useState<ProjectContext>({
    ...DEFAULT_CONTEXT,
  });
  const [customTech, setCustomTech] = useState('');
  const [customLabel, setCustomLabel] = useState('');

  // Step 1: Tech Stack selection
  const toggleTech = useCallback((tech: string) => {
    setContextState((prev) => ({
      ...prev,
      techStack: prev.techStack.includes(tech)
        ? prev.techStack.filter((t) => t !== tech)
        : [...prev.techStack, tech],
    }));
  }, []);

  const addCustomTech = useCallback(() => {
    if (customTech.trim() && !context.techStack.includes(customTech.trim())) {
      setContextState((prev) => ({
        ...prev,
        techStack: [...prev.techStack, customTech.trim()],
      }));
      setCustomTech('');
    }
  }, [customTech, context.techStack]);

  // Step 3: Labels
  const toggleLabel = useCallback((label: string) => {
    setContextState((prev) => ({
      ...prev,
      defaultLabels: prev.defaultLabels.includes(label)
        ? prev.defaultLabels.filter((l) => l !== label)
        : [...prev.defaultLabels, label],
    }));
  }, []);

  const addCustomLabel = useCallback(() => {
    if (customLabel.trim() && !context.defaultLabels.includes(customLabel.trim())) {
      setContextState((prev) => ({
        ...prev,
        defaultLabels: [...prev.defaultLabels, customLabel.trim()],
      }));
      setCustomLabel('');
    }
  }, [customLabel, context.defaultLabels]);

  // Navigation
  const nextStep = useCallback(() => {
    if (step < 3) setStep(step + 1);
  }, [step]);

  const prevStep = useCallback(() => {
    if (step > 1) setStep(step - 1);
  }, [step]);

  // Complete wizard
  const handleComplete = useCallback(async () => {
    if (!boardId) return;
    try {
      await setContext(boardId, context);
      onComplete?.();
      onClose();
    } catch (error) {
      console.error('Failed to save project context:', error);
    }
  }, [boardId, context, setContext, onComplete, onClose]);

  // Skip wizard
  const handleSkip = useCallback(() => {
    onClose();
  }, [onClose]);

  return (
    <AnimatePresence>
      {open && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={handleSkip}
            className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50"
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4"
          >
            <div
              className={cn(
                'w-full max-w-2xl',
                'bg-bg-secondary border border-border-subtle',
                'rounded-2xl shadow-2xl',
                'flex flex-col overflow-hidden'
              )}
              onClick={(e) => e.stopPropagation()}
            >
              {/* Header */}
              <div className="flex items-center justify-between px-6 py-4 border-b border-border-subtle">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500/30 to-purple-500/30 flex items-center justify-center">
                    <Sparkles className="w-5 h-5 text-accent" />
                  </div>
                  <div>
                    <h2 className="text-lg font-bold text-text-primary font-display">
                      Setup Project Context
                    </h2>
                    <p className="text-xs text-text-muted">
                      Help AI understand your project better
                    </p>
                  </div>
                </div>

                <button
                  onClick={handleSkip}
                  className="w-8 h-8 rounded-lg flex items-center justify-center text-text-tertiary hover:text-text-primary hover:bg-bg-hover transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Progress Steps */}
              <div className="flex items-center justify-center gap-2 px-6 py-4 border-b border-border-subtle bg-bg-primary">
                {STEPS.map((s, index) => {
                  const Icon = s.icon;
                  const isActive = step === s.id;
                  const isCompleted = step > s.id;

                  return (
                    <div key={s.id} className="flex items-center">
                      <div
                        className={cn(
                          'flex items-center gap-2 px-3 py-1.5 rounded-lg transition-colors',
                          isActive
                            ? 'bg-accent-muted text-accent'
                            : isCompleted
                            ? 'text-status-success'
                            : 'text-text-muted'
                        )}
                      >
                        {isCompleted ? (
                          <Check className="w-4 h-4" />
                        ) : (
                          <Icon className="w-4 h-4" />
                        )}
                        <span className="text-sm font-medium">{s.title}</span>
                      </div>
                      {index < STEPS.length - 1 && (
                        <ChevronRight className="w-4 h-4 text-text-muted mx-2" />
                      )}
                    </div>
                  );
                })}
              </div>

              {/* Content */}
              <div className="flex-1 p-6 overflow-y-auto max-h-[60vh]">
                <AnimatePresence mode="wait">
                  {step === 1 && (
                    <motion.div
                      key="step1"
                      initial={{ opacity: 0, x: 20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -20 }}
                      className="space-y-6"
                    >
                      {/* Project Description */}
                      <div>
                        <label className="block text-sm font-medium text-text-primary mb-2">
                          Project Description
                        </label>
                        <textarea
                          value={context.description || ''}
                          onChange={(e) =>
                            setContextState((prev) => ({
                              ...prev,
                              description: e.target.value || undefined,
                            }))
                          }
                          placeholder="Briefly describe your project (e.g., A desktop kanban app with AI features...)"
                          rows={3}
                          className={cn(
                            'w-full px-3 py-2 bg-bg-tertiary border border-border-subtle rounded-lg',
                            'text-sm text-text-primary placeholder:text-text-muted resize-none',
                            'focus:outline-none focus:border-accent focus:ring-2 focus:ring-accent/20'
                          )}
                        />
                      </div>

                      {/* Tech Stack */}
                      <div>
                        <label className="block text-sm font-medium text-text-primary mb-2">
                          Tech Stack
                        </label>
                        <p className="text-xs text-text-muted mb-3">
                          Select technologies used in your project
                        </p>
                        <div className="flex flex-wrap gap-2 mb-3">
                          {TECH_STACK_OPTIONS.map((tech) => {
                            const isSelected = context.techStack.includes(tech.label);
                            return (
                              <button
                                key={tech.label}
                                onClick={() => toggleTech(tech.label)}
                                className={cn(
                                  'px-3 py-1.5 rounded-lg text-xs font-medium transition-colors',
                                  isSelected
                                    ? 'bg-accent text-white'
                                    : 'bg-bg-tertiary text-text-secondary hover:bg-bg-hover'
                                )}
                              >
                                {tech.label}
                              </button>
                            );
                          })}
                        </div>

                        {/* Custom tech */}
                        <div className="flex gap-2">
                          <input
                            type="text"
                            value={customTech}
                            onChange={(e) => setCustomTech(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && addCustomTech()}
                            placeholder="Add custom..."
                            className={cn(
                              'flex-1 px-3 py-2 bg-bg-tertiary border border-border-subtle rounded-lg',
                              'text-sm text-text-primary placeholder:text-text-muted',
                              'focus:outline-none focus:border-accent'
                            )}
                          />
                          <button
                            onClick={addCustomTech}
                            disabled={!customTech.trim()}
                            className={cn(
                              'px-3 py-2 rounded-lg bg-accent text-white',
                              'disabled:opacity-50 disabled:cursor-not-allowed'
                            )}
                          >
                            <Plus className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    </motion.div>
                  )}

                  {step === 2 && (
                    <motion.div
                      key="step2"
                      initial={{ opacity: 0, x: 20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -20 }}
                      className="space-y-6"
                    >
                      {/* Architecture */}
                      <div>
                        <label className="block text-sm font-medium text-text-primary mb-2">
                          Architecture
                        </label>
                        <textarea
                          value={context.architecture || ''}
                          onChange={(e) =>
                            setContextState((prev) => ({
                              ...prev,
                              architecture: e.target.value || undefined,
                            }))
                          }
                          placeholder="Describe your project architecture (e.g., Monorepo with React frontend, Rust backend via Tauri, Python AI agent...)"
                          rows={3}
                          className={cn(
                            'w-full px-3 py-2 bg-bg-tertiary border border-border-subtle rounded-lg',
                            'text-sm text-text-primary placeholder:text-text-muted resize-none',
                            'focus:outline-none focus:border-accent focus:ring-2 focus:ring-accent/20'
                          )}
                        />
                      </div>

                      {/* Conventions */}
                      <div>
                        <label className="block text-sm font-medium text-text-primary mb-2">
                          Coding Conventions
                        </label>
                        <textarea
                          value={context.conventions || ''}
                          onChange={(e) =>
                            setContextState((prev) => ({
                              ...prev,
                              conventions: e.target.value || undefined,
                            }))
                          }
                          placeholder="Describe your coding conventions (e.g., Use kebab-case for files, PascalCase for components, always write tests...)"
                          rows={3}
                          className={cn(
                            'w-full px-3 py-2 bg-bg-tertiary border border-border-subtle rounded-lg',
                            'text-sm text-text-primary placeholder:text-text-muted resize-none',
                            'focus:outline-none focus:border-accent focus:ring-2 focus:ring-accent/20'
                          )}
                        />
                      </div>
                    </motion.div>
                  )}

                  {step === 3 && (
                    <motion.div
                      key="step3"
                      initial={{ opacity: 0, x: 20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -20 }}
                      className="space-y-6"
                    >
                      {/* Default Labels */}
                      <div>
                        <label className="block text-sm font-medium text-text-primary mb-2">
                          Default Labels for AI
                        </label>
                        <p className="text-xs text-text-muted mb-3">
                          Select labels the AI can suggest when triaging tickets
                        </p>
                        <div className="flex flex-wrap gap-2 mb-3">
                          {LABEL_SUGGESTIONS.map((label) => {
                            const isSelected = context.defaultLabels.includes(label);
                            return (
                              <button
                                key={label}
                                onClick={() => toggleLabel(label)}
                                className={cn(
                                  'px-3 py-1.5 rounded-lg text-xs font-medium transition-colors',
                                  isSelected
                                    ? 'bg-accent text-white'
                                    : 'bg-bg-tertiary text-text-secondary hover:bg-bg-hover'
                                )}
                              >
                                {label}
                              </button>
                            );
                          })}
                        </div>

                        {/* Custom label */}
                        <div className="flex gap-2">
                          <input
                            type="text"
                            value={customLabel}
                            onChange={(e) => setCustomLabel(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && addCustomLabel()}
                            placeholder="Add custom label..."
                            className={cn(
                              'flex-1 px-3 py-2 bg-bg-tertiary border border-border-subtle rounded-lg',
                              'text-sm text-text-primary placeholder:text-text-muted',
                              'focus:outline-none focus:border-accent'
                            )}
                          />
                          <button
                            onClick={addCustomLabel}
                            disabled={!customLabel.trim()}
                            className={cn(
                              'px-3 py-2 rounded-lg bg-accent text-white',
                              'disabled:opacity-50 disabled:cursor-not-allowed'
                            )}
                          >
                            <Plus className="w-4 h-4" />
                          </button>
                        </div>
                      </div>

                      {/* Summary Preview */}
                      <div className="p-4 rounded-xl bg-gradient-to-r from-indigo-500/10 to-purple-500/10 border border-accent/20">
                        <h4 className="text-sm font-medium text-text-primary mb-3 flex items-center gap-2">
                          <Sparkles className="w-4 h-4 text-accent" />
                          AI Context Summary
                        </h4>
                        <div className="space-y-2 text-xs text-text-secondary">
                          {context.description && (
                            <p>
                              <span className="text-text-muted">Project:</span>{' '}
                              {context.description.slice(0, 50)}
                              {context.description.length > 50 ? '...' : ''}
                            </p>
                          )}
                          {context.techStack.length > 0 && (
                            <p>
                              <span className="text-text-muted">Tech:</span>{' '}
                              {context.techStack.join(', ')}
                            </p>
                          )}
                          {context.defaultLabels.length > 0 && (
                            <p>
                              <span className="text-text-muted">Labels:</span>{' '}
                              {context.defaultLabels.join(', ')}
                            </p>
                          )}
                          {!context.description &&
                            context.techStack.length === 0 &&
                            context.defaultLabels.length === 0 && (
                              <p className="text-text-muted italic">
                                No context configured yet
                              </p>
                            )}
                        </div>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>

              {/* Footer */}
              <div className="flex items-center justify-between px-6 py-4 border-t border-border-subtle">
                <button
                  onClick={handleSkip}
                  className="text-sm text-text-muted hover:text-text-secondary transition-colors"
                >
                  Skip for now
                </button>

                <div className="flex gap-3">
                  {step > 1 && (
                    <button
                      onClick={prevStep}
                      className={cn(
                        'flex items-center gap-2 px-4 py-2 rounded-lg',
                        'text-sm font-medium text-text-secondary',
                        'hover:bg-bg-hover transition-colors'
                      )}
                    >
                      <ChevronLeft className="w-4 h-4" />
                      Back
                    </button>
                  )}

                  {step < 3 ? (
                    <button
                      onClick={nextStep}
                      className={cn(
                        'flex items-center gap-2 px-4 py-2 rounded-lg',
                        'bg-accent text-white font-medium text-sm',
                        'hover:bg-accent/90 transition-colors'
                      )}
                    >
                      Next
                      <ChevronRight className="w-4 h-4" />
                    </button>
                  ) : (
                    <button
                      onClick={handleComplete}
                      disabled={isLoading}
                      className={cn(
                        'flex items-center gap-2 px-4 py-2 rounded-lg',
                        'bg-status-success text-white font-medium text-sm',
                        'hover:bg-status-success/90 transition-colors',
                        'disabled:opacity-50 disabled:cursor-not-allowed'
                      )}
                    >
                      {isLoading ? (
                        <>
                          <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                          Saving...
                        </>
                      ) : (
                        <>
                          <Check className="w-4 h-4" />
                          Complete Setup
                        </>
                      )}
                    </button>
                  )}
                </div>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
