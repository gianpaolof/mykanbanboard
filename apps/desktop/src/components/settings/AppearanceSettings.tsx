// components/settings/AppearanceSettings.tsx - Theme settings
import { Sun, Moon, Monitor } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useThemeStore, type Theme } from '@/stores/themeStore';
import { SettingsSection } from './SettingsSection';

const THEME_OPTIONS: { value: Theme; label: string; icon: typeof Sun }[] = [
  { value: 'light', label: 'Light', icon: Sun },
  { value: 'dark', label: 'Dark', icon: Moon },
  { value: 'system', label: 'System', icon: Monitor },
];

export function AppearanceSettings() {
  const theme = useThemeStore((state) => state.theme);
  const setTheme = useThemeStore((state) => state.setTheme);

  return (
    <div className="space-y-8">
      <SettingsSection
        title="Theme"
        description="Choose how Kanban AI looks"
      >
        <div className="grid grid-cols-3 gap-3">
          {THEME_OPTIONS.map((option) => {
            const Icon = option.icon;
            const isSelected = theme === option.value;

            return (
              <button
                key={option.value}
                onClick={() => setTheme(option.value)}
                className={cn(
                  'flex flex-col items-center gap-3 p-4 rounded-xl border-2 transition-all',
                  'hover:bg-bg-hover',
                  isSelected
                    ? 'border-accent bg-accent-muted'
                    : 'border-border-subtle bg-bg-elevated'
                )}
              >
                <div
                  className={cn(
                    'w-12 h-12 rounded-lg flex items-center justify-center',
                    isSelected
                      ? 'bg-accent/20 text-accent'
                      : 'bg-bg-tertiary text-text-tertiary'
                  )}
                >
                  <Icon className="w-6 h-6" />
                </div>
                <span
                  className={cn(
                    'text-sm font-medium',
                    isSelected ? 'text-text-primary' : 'text-text-tertiary'
                  )}
                >
                  {option.label}
                </span>
              </button>
            );
          })}
        </div>
      </SettingsSection>
    </div>
  );
}
