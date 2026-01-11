// components/settings/AISettings.tsx - AI API configuration
import { useState } from 'react';
import { Eye, EyeOff, AlertCircle, CheckCircle2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useSettingsStore } from '@/stores/settingsStore';
import { SettingsSection } from './SettingsSection';
import { SettingsToggle } from './SettingsToggle';
import type { AIModel } from '@/types/settings';

const AI_MODELS: { value: AIModel; label: string; description: string }[] = [
  {
    value: 'claude-3-5-sonnet',
    label: 'Claude 3.5 Sonnet',
    description: 'Best balance of speed and capability',
  },
  {
    value: 'claude-3-opus',
    label: 'Claude 3 Opus',
    description: 'Most capable, slower',
  },
  {
    value: 'gpt-4-turbo',
    label: 'GPT-4 Turbo',
    description: 'Fast OpenAI model',
  },
  {
    value: 'gpt-4',
    label: 'GPT-4',
    description: 'OpenAI standard model',
  },
];

export function AISettings() {
  const apiKey = useSettingsStore((state) => state.ai.apiKey);
  const model = useSettingsStore((state) => state.ai.model);
  const setAIApiKey = useSettingsStore((state) => state.setAIApiKey);
  const setAIModel = useSettingsStore((state) => state.setAIModel);
  const enableAITriage = useSettingsStore((state) => state.board.enableAITriage);
  const toggleAITriage = useSettingsStore((state) => state.toggleAITriage);
  const autoAssignPriority = useSettingsStore((state) => state.board.autoAssignPriority);
  const toggleAutoAssignPriority = useSettingsStore((state) => state.toggleAutoAssignPriority);

  const [showApiKey, setShowApiKey] = useState(false);

  const isConfigured = apiKey.length > 0;

  return (
    <div className="space-y-8">
      {/* API Key */}
      <SettingsSection
        title="API Configuration"
        description="Configure your AI provider credentials"
      >
        <div className="space-y-3">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wide text-text-muted mb-2">
              API Key
            </label>
            <div className="relative">
              <input
                type={showApiKey ? 'text' : 'password'}
                value={apiKey}
                onChange={(e) => setAIApiKey(e.target.value)}
                placeholder="sk-ant-..."
                className={cn(
                  'w-full px-4 py-2.5 pr-10',
                  'bg-bg-tertiary border border-border-subtle rounded-lg',
                  'text-sm text-text-primary placeholder:text-text-muted',
                  'focus:outline-none focus:border-accent focus:ring-2 focus:ring-accent/20',
                  'font-mono'
                )}
              />
              <button
                type="button"
                onClick={() => setShowApiKey(!showApiKey)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-text-tertiary hover:text-text-secondary"
              >
                {showApiKey ? (
                  <EyeOff className="w-4 h-4" />
                ) : (
                  <Eye className="w-4 h-4" />
                )}
              </button>
            </div>
          </div>

          {/* Status indicator */}
          <div
            className={cn(
              'flex items-center gap-2 px-3 py-2 rounded-lg text-xs',
              isConfigured
                ? 'bg-status-success/10 text-status-success'
                : 'bg-status-warning/10 text-status-warning'
            )}
          >
            {isConfigured ? (
              <>
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>API key configured</span>
              </>
            ) : (
              <>
                <AlertCircle className="w-3.5 h-3.5" />
                <span>No API key configured - AI features disabled</span>
              </>
            )}
          </div>
        </div>
      </SettingsSection>

      {/* Model Selection */}
      <SettingsSection
        title="AI Model"
        description="Choose which language model to use"
      >
        <div className="space-y-2">
          {AI_MODELS.map((option) => {
            const isSelected = model === option.value;

            return (
              <button
                key={option.value}
                onClick={() => setAIModel(option.value)}
                className={cn(
                  'w-full flex items-start gap-3 p-3 rounded-lg border transition-all text-left',
                  'hover:bg-bg-hover',
                  isSelected
                    ? 'border-accent bg-accent-muted'
                    : 'border-border-subtle bg-bg-elevated'
                )}
              >
                <div
                  className={cn(
                    'w-5 h-5 rounded-full border-2 mt-0.5 flex items-center justify-center flex-shrink-0',
                    isSelected ? 'border-accent' : 'border-border-strong'
                  )}
                >
                  {isSelected && (
                    <div className="w-2.5 h-2.5 rounded-full bg-accent" />
                  )}
                </div>
                <div className="flex-1">
                  <div
                    className={cn(
                      'text-sm font-medium',
                      isSelected ? 'text-text-primary' : 'text-text-secondary'
                    )}
                  >
                    {option.label}
                  </div>
                  <div className="text-xs text-text-muted mt-0.5">
                    {option.description}
                  </div>
                </div>
              </button>
            );
          })}
        </div>
      </SettingsSection>

      {/* AI Features */}
      <SettingsSection
        title="AI Features"
        description="Enable or disable AI-powered features"
      >
        <SettingsToggle
          label="Auto-triage new tickets"
          description="Automatically suggest priority, effort, and labels"
          checked={enableAITriage}
          onChange={toggleAITriage}
        />
        <SettingsToggle
          label="Auto-assign priority"
          description="Let AI determine ticket priority based on content"
          checked={autoAssignPriority}
          onChange={toggleAutoAssignPriority}
        />
      </SettingsSection>
    </div>
  );
}
