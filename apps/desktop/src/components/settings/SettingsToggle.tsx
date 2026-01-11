// components/settings/SettingsToggle.tsx - Toggle switch for settings
import { cn } from '@/lib/utils';

interface SettingsToggleProps {
  label: string;
  description?: string;
  checked: boolean;
  onChange: () => void;
}

export function SettingsToggle({
  label,
  description,
  checked,
  onChange,
}: SettingsToggleProps) {
  return (
    <label className="flex items-center justify-between p-4 rounded-lg bg-bg-elevated border border-border-subtle hover:bg-bg-hover transition-colors cursor-pointer">
      <div>
        <div className="text-sm font-medium text-text-primary">{label}</div>
        {description && (
          <div className="text-xs text-text-tertiary mt-0.5">{description}</div>
        )}
      </div>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        onClick={onChange}
        className={cn(
          'relative w-11 h-6 rounded-full transition-colors',
          checked ? 'bg-accent' : 'bg-bg-tertiary'
        )}
      >
        <div
          className={cn(
            'absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full transition-transform shadow-sm',
            checked && 'translate-x-5'
          )}
        />
      </button>
    </label>
  );
}
