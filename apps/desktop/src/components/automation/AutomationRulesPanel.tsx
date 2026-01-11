// components/automation/AutomationRulesPanel.tsx
import { useState, useEffect, useCallback, memo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  X,
  Plus,
  Zap,
  Power,
  Trash2,
  Sparkles,
  Clock,
  ArrowRight,
} from 'lucide-react';
import { toast } from 'sonner';
import { cn } from '@/lib/utils';
import { automationApi } from '@/lib/tauri';
import { useBoardStore } from '@/stores/boardStore';
import type { AutomationRule, TriggerType, ActionType } from '@/types';

interface AutomationRulesPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

const TRIGGER_LABELS: Record<TriggerType, string> = {
  ticket_created: 'Ticket Created',
  ticket_moved: 'Ticket Moved',
  ticket_updated: 'Ticket Updated',
  label_added: 'Label Added',
  label_removed: 'Label Removed',
  due_date_approaching: 'Due Date Approaching',
  priority_changed: 'Priority Changed',
};

const ACTION_LABELS: Record<ActionType, string> = {
  move_ticket: 'Move Ticket',
  set_priority: 'Set Priority',
  add_label: 'Add Label',
  remove_label: 'Remove Label',
  set_due_date: 'Set Due Date',
  notify: 'Send Notification',
  auto_triage: 'AI Triage',
};

const TRIGGER_ICONS: Record<TriggerType, string> = {
  ticket_created: '📝',
  ticket_moved: '➡️',
  ticket_updated: '✏️',
  label_added: '🏷️',
  label_removed: '🚫',
  due_date_approaching: '⏰',
  priority_changed: '🔥',
};

const ACTION_ICONS: Record<ActionType, string> = {
  move_ticket: '📦',
  set_priority: '⚡',
  add_label: '🏷️',
  remove_label: '🗑️',
  set_due_date: '📅',
  notify: '🔔',
  auto_triage: '🤖',
};

export const AutomationRulesPanel = memo(function AutomationRulesPanel({
  isOpen,
  onClose,
}: AutomationRulesPanelProps) {
  const [rules, setRules] = useState<AutomationRule[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [naturalLanguageInput, setNaturalLanguageInput] = useState('');
  const [isParsing, setIsParsing] = useState(false);

  const currentBoardId = useBoardStore((state) => state.currentBoardId);

  // Load rules
  const loadRules = useCallback(async () => {
    if (!currentBoardId) return;

    setIsLoading(true);
    try {
      const loadedRules = await automationApi.getRules(currentBoardId);
      setRules(loadedRules);
    } catch (error) {
      console.error('Failed to load automation rules:', error);
      toast.error('Failed to load automation rules');
    } finally {
      setIsLoading(false);
    }
  }, [currentBoardId]);

  useEffect(() => {
    if (isOpen) {
      loadRules();
    }
  }, [isOpen, loadRules]);

  // Toggle rule
  const handleToggleRule = async (rule: AutomationRule) => {
    try {
      const updated = await automationApi.toggleRule(rule.id);
      setRules((prev) =>
        prev.map((r) => (r.id === updated.id ? updated : r))
      );
      toast.success(
        `Rule "${rule.name}" ${updated.enabled ? 'enabled' : 'disabled'}`
      );
    } catch (error) {
      console.error('Failed to toggle rule:', error);
      toast.error('Failed to toggle rule');
    }
  };

  // Delete rule
  const handleDeleteRule = async (rule: AutomationRule) => {
    try {
      await automationApi.deleteRule(rule.id);
      setRules((prev) => prev.filter((r) => r.id !== rule.id));
      toast.success(`Rule "${rule.name}" deleted`);
    } catch (error) {
      console.error('Failed to delete rule:', error);
      toast.error('Failed to delete rule');
    }
  };

  // Parse natural language and create rule
  const handleCreateFromNaturalLanguage = async () => {
    if (!naturalLanguageInput.trim() || !currentBoardId) return;

    setIsParsing(true);
    try {
      // Call agent API to parse the rule
      const response = await fetch('http://localhost:8765/api/parse-rule', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          natural_language: naturalLanguageInput,
          board_context: {},
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to parse rule');
      }

      const parsed = await response.json();

      // Create the rule with parsed data
      const newRule = await automationApi.createRule({
        boardId: currentBoardId,
        name: parsed.rule_name,
        description: naturalLanguageInput,
        triggerType: parsed.trigger_type,
        triggerConfig: parsed.trigger_config,
        actionType: parsed.action_type,
        actionConfig: parsed.action_config,
      });

      setRules((prev) => [newRule, ...prev]);
      setNaturalLanguageInput('');
      setShowCreateForm(false);
      toast.success(`Rule "${newRule.name}" created`);
    } catch (error) {
      console.error('Failed to create rule:', error);
      toast.error('Failed to parse or create rule. Make sure the AI agent is running.');
    } finally {
      setIsParsing(false);
    }
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      >
        <motion.div
          initial={{ scale: 0.95, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.95, opacity: 0 }}
          onClick={(e) => e.stopPropagation()}
          className={cn(
            'w-full max-w-2xl max-h-[80vh] overflow-hidden',
            'bg-bg-secondary rounded-xl border border-border-subtle',
            'shadow-2xl'
          )}
        >
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-border-subtle">
            <div className="flex items-center gap-2">
              <Zap className="w-5 h-5 text-accent" />
              <h2 className="text-lg font-semibold text-text-primary">
                Automation Rules
              </h2>
              <span className="text-xs text-text-muted bg-bg-tertiary px-2 py-0.5 rounded-full">
                {rules.length}
              </span>
            </div>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-text-tertiary hover:text-text-primary hover:bg-bg-hover transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Content */}
          <div className="p-4 overflow-y-auto max-h-[calc(80vh-140px)]">
            {/* Create New Rule */}
            {showCreateForm ? (
              <div className="mb-4 p-4 rounded-lg bg-bg-elevated border border-border-subtle">
                <div className="flex items-center gap-2 mb-3">
                  <Sparkles className="w-4 h-4 text-purple-400" />
                  <span className="text-sm font-medium text-text-primary">
                    Create with Natural Language
                  </span>
                </div>
                <textarea
                  value={naturalLanguageInput}
                  onChange={(e) => setNaturalLanguageInput(e.target.value)}
                  placeholder='Example: "When a ticket is moved to Done, add the completed label"'
                  className={cn(
                    'w-full h-24 p-3 rounded-lg resize-none',
                    'bg-bg-tertiary border border-border-subtle',
                    'text-sm text-text-primary placeholder:text-text-muted',
                    'focus:outline-none focus:border-accent'
                  )}
                />
                <div className="flex items-center justify-end gap-2 mt-3">
                  <button
                    onClick={() => {
                      setShowCreateForm(false);
                      setNaturalLanguageInput('');
                    }}
                    className="px-3 py-1.5 text-sm text-text-secondary hover:text-text-primary transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleCreateFromNaturalLanguage}
                    disabled={isParsing || !naturalLanguageInput.trim()}
                    className={cn(
                      'flex items-center gap-2 px-4 py-1.5 rounded-lg',
                      'bg-accent text-white text-sm font-medium',
                      'hover:bg-accent/90 transition-colors',
                      'disabled:opacity-50 disabled:cursor-not-allowed'
                    )}
                  >
                    {isParsing ? (
                      <>
                        <div className="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        Parsing...
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-3.5 h-3.5" />
                        Create Rule
                      </>
                    )}
                  </button>
                </div>
              </div>
            ) : (
              <button
                onClick={() => setShowCreateForm(true)}
                className={cn(
                  'w-full mb-4 p-3 rounded-lg',
                  'border-2 border-dashed border-border-subtle',
                  'text-text-secondary hover:text-text-primary',
                  'hover:border-accent/50 hover:bg-accent/5',
                  'transition-all flex items-center justify-center gap-2'
                )}
              >
                <Plus className="w-4 h-4" />
                <span className="text-sm">Add Automation Rule</span>
              </button>
            )}

            {/* Rules List */}
            {isLoading ? (
              <div className="flex items-center justify-center py-12">
                <div className="w-6 h-6 border-2 border-accent border-t-transparent rounded-full animate-spin" />
              </div>
            ) : rules.length === 0 ? (
              <div className="text-center py-12">
                <Zap className="w-12 h-12 mx-auto text-text-muted mb-3" />
                <p className="text-text-secondary text-sm">
                  No automation rules yet
                </p>
                <p className="text-text-muted text-xs mt-1">
                  Create rules using natural language to automate your workflow
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {rules.map((rule) => (
                  <motion.div
                    key={rule.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className={cn(
                      'p-4 rounded-lg',
                      'bg-bg-elevated border border-border-subtle',
                      'hover:border-border-DEFAULT transition-colors',
                      !rule.enabled && 'opacity-60'
                    )}
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-medium text-text-primary truncate">
                            {rule.name}
                          </span>
                          {!rule.enabled && (
                            <span className="text-xs text-text-muted px-1.5 py-0.5 bg-bg-tertiary rounded">
                              Disabled
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-text-muted mb-2 line-clamp-2">
                          {rule.description}
                        </p>

                        {/* Trigger -> Action */}
                        <div className="flex items-center gap-2 text-xs">
                          <span
                            className={cn(
                              'flex items-center gap-1 px-2 py-1 rounded',
                              'bg-purple-500/10 text-purple-400'
                            )}
                          >
                            <span>{TRIGGER_ICONS[rule.triggerType]}</span>
                            {TRIGGER_LABELS[rule.triggerType]}
                          </span>
                          <ArrowRight className="w-3 h-3 text-text-muted" />
                          <span
                            className={cn(
                              'flex items-center gap-1 px-2 py-1 rounded',
                              'bg-blue-500/10 text-blue-400'
                            )}
                          >
                            <span>{ACTION_ICONS[rule.actionType]}</span>
                            {ACTION_LABELS[rule.actionType]}
                          </span>
                        </div>

                        {/* Stats */}
                        {rule.triggerCount > 0 && (
                          <div className="flex items-center gap-3 mt-2 text-xs text-text-muted">
                            <span className="flex items-center gap-1">
                              <Clock className="w-3 h-3" />
                              Triggered {rule.triggerCount} time
                              {rule.triggerCount !== 1 ? 's' : ''}
                            </span>
                          </div>
                        )}
                      </div>

                      {/* Actions */}
                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => handleToggleRule(rule)}
                          className={cn(
                            'p-1.5 rounded-lg transition-colors',
                            rule.enabled
                              ? 'text-green-400 hover:bg-green-500/10'
                              : 'text-text-muted hover:bg-bg-hover'
                          )}
                          title={rule.enabled ? 'Disable' : 'Enable'}
                        >
                          <Power className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleDeleteRule(rule)}
                          className="p-1.5 rounded-lg text-text-muted hover:text-red-400 hover:bg-red-500/10 transition-colors"
                          title="Delete"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="p-3 border-t border-border-subtle bg-bg-tertiary/50">
            <p className="text-xs text-text-muted text-center">
              Rules automatically execute when their trigger conditions are met
            </p>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
});
