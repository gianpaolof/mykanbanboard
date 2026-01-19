// components/settings/SettingsModal.tsx - Main settings modal
import { useState, memo, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Palette, Bot, Keyboard, Database, Sparkles } from 'lucide-react';
import { cn } from '@/lib/utils';
import { AppearanceSettings } from './AppearanceSettings';
import { AISettings } from './AISettings';
import { KeyboardShortcutsSettings } from './KeyboardShortcutsSettings';
import { DataManagementSettings } from './DataManagementSettings';
import { ProjectSettings } from './ProjectSettings';

interface SettingsModalProps {
  open: boolean;
  onClose: () => void;
}

type SettingsTab = 'appearance' | 'ai' | 'project' | 'data' | 'shortcuts';

const TABS: { id: SettingsTab; label: string; icon: typeof Palette }[] = [
  { id: 'appearance', label: 'Appearance', icon: Palette },
  { id: 'ai', label: 'AI Agent', icon: Bot },
  { id: 'project', label: 'Project', icon: Sparkles },
  { id: 'data', label: 'Data', icon: Database },
  { id: 'shortcuts', label: 'Shortcuts', icon: Keyboard },
];

export const SettingsModal = memo(function SettingsModal({
  open,
  onClose,
}: SettingsModalProps) {
  const [activeTab, setActiveTab] = useState<SettingsTab>('appearance');

  // Handle escape key to close
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && open) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [open, onClose]);

  return (
    <AnimatePresence>
      {open && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50"
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4"
            onClick={(e) => e.stopPropagation()}
          >
            <div
              className={cn(
                'w-full max-w-4xl max-h-[85vh]',
                'bg-bg-secondary border border-border-subtle',
                'rounded-2xl shadow-2xl',
                'flex flex-col overflow-hidden'
              )}
              onClick={(e) => e.stopPropagation()}
            >
              {/* Header */}
              <div className="flex items-center justify-between px-6 py-4 border-b border-border-subtle">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500/20 to-purple-500/20 flex items-center justify-center">
                    <Palette className="w-4 h-4 text-accent" />
                  </div>
                  <h2 className="text-xl font-bold text-text-primary font-display">
                    Settings
                  </h2>
                </div>

                <button
                  onClick={onClose}
                  className="w-8 h-8 rounded-lg flex items-center justify-center text-text-tertiary hover:text-text-primary hover:bg-bg-hover transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Content */}
              <div className="flex flex-1 overflow-hidden">
                {/* Sidebar Tabs */}
                <div className="w-48 border-r border-border-subtle bg-bg-primary p-3 space-y-1">
                  {TABS.map((tab) => {
                    const Icon = tab.icon;
                    const isActive = activeTab === tab.id;

                    return (
                      <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={cn(
                          'w-full flex items-center gap-3 px-3 py-2.5 rounded-lg',
                          'text-sm font-medium transition-all',
                          isActive
                            ? 'bg-accent-muted text-accent'
                            : 'text-text-tertiary hover:bg-bg-hover hover:text-text-secondary'
                        )}
                      >
                        <Icon className="w-4 h-4" />
                        <span>{tab.label}</span>
                      </button>
                    );
                  })}
                </div>

                {/* Tab Content */}
                <div className="flex-1 overflow-y-auto p-6">
                  <AnimatePresence mode="wait">
                    <motion.div
                      key={activeTab}
                      initial={{ opacity: 0, x: 20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -20 }}
                      transition={{ duration: 0.2 }}
                    >
                      {activeTab === 'appearance' && <AppearanceSettings />}
                      {activeTab === 'ai' && <AISettings />}
                      {activeTab === 'project' && <ProjectSettings />}
                      {activeTab === 'data' && <DataManagementSettings />}
                      {activeTab === 'shortcuts' && <KeyboardShortcutsSettings />}
                    </motion.div>
                  </AnimatePresence>
                </div>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
});
