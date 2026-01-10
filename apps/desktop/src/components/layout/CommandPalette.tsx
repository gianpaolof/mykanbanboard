import { useEffect } from 'react';
import { Command } from 'cmdk';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Search,
  Plus,
  Sparkles,
  FileText,
  LayoutGrid,
  List,
  Calendar,
  Settings,
  Clock,
} from 'lucide-react';
import { cn } from '../../lib/utils';

export interface CommandPaletteProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onCreateTicket: () => void;
  onOpenAI: () => void;
  onSwitchView: (view: 'board' | 'list' | 'timeline') => void;
}

// Mock data for recent tickets - in production, this would come from a store/API
const RECENT_TICKETS = [
  { id: '1', title: 'Implement authentication flow', priority: 'high' as const },
  { id: '2', title: 'Design dashboard wireframes', priority: 'medium' as const },
  { id: '3', title: 'Fix navigation bug', priority: 'critical' as const },
  { id: '4', title: 'Update documentation', priority: 'low' as const },
];

const priorityColors = {
  critical: 'text-red-400',
  high: 'text-orange-400',
  medium: 'text-yellow-400',
  low: 'text-blue-400',
};

export function CommandPalette({
  open,
  onOpenChange,
  onCreateTicket,
  onOpenAI,
  onSwitchView,
}: CommandPaletteProps) {
  // Close on Escape
  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onOpenChange(false);
      }
    };

    document.addEventListener('keydown', down);
    return () => document.removeEventListener('keydown', down);
  }, [onOpenChange]);

  const handleAction = (action: () => void) => {
    action();
    onOpenChange(false);
  };

  return (
    <AnimatePresence>
      {open && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm"
            onClick={() => onOpenChange(false)}
          />

          {/* Command Dialog */}
          <div className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh]">
            <motion.div
              initial={{ opacity: 0, scale: 0.96, y: -20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.96, y: -20 }}
              transition={{ duration: 0.15, ease: 'easeOut' }}
              className="w-full max-w-[560px]"
            >
              <Command
                className={cn(
                  'overflow-hidden rounded-xl border border-border',
                  'bg-bg-secondary shadow-xl',
                  'backdrop-blur-xl'
                )}
                loop
              >
                {/* Search Input */}
                <div className="flex items-center border-b border-border px-4">
                  <Search className="mr-3 h-4 w-4 shrink-0 text-zinc-500" />
                  <Command.Input
                    placeholder="Type a command or search..."
                    className={cn(
                      'flex h-12 w-full bg-transparent',
                      'text-sm text-zinc-100 placeholder:text-zinc-500',
                      'outline-none disabled:cursor-not-allowed disabled:opacity-50'
                    )}
                  />
                </div>

                <Command.List className="max-h-[400px] overflow-y-auto overflow-x-hidden p-2">
                  <Command.Empty className="py-6 text-center text-sm text-zinc-500">
                    No results found.
                  </Command.Empty>

                  {/* Actions Group */}
                  <Command.Group
                    heading="Actions"
                    className="[&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5 [&_[cmdk-group-heading]]:text-xs [&_[cmdk-group-heading]]:font-medium [&_[cmdk-group-heading]]:text-zinc-500"
                  >
                    <CommandItem
                      onSelect={() => handleAction(onCreateTicket)}
                      icon={<Plus className="h-4 w-4" />}
                      label="Create new ticket"
                      shortcut={['⌘', 'N']}
                    />
                    <CommandItem
                      onSelect={() => handleAction(onOpenAI)}
                      icon={<Sparkles className="h-4 w-4 text-indigo-400" />}
                      label="Ask AI assistant"
                      shortcut={['⌘', '⇧', 'A']}
                    />
                    <CommandItem
                      onSelect={() => handleAction(() => console.log('Daily summary'))}
                      icon={<FileText className="h-4 w-4" />}
                      label="Get daily summary"
                      shortcut={['⌘', '⇧', 'S']}
                    />
                  </Command.Group>

                  {/* Navigation Group */}
                  <Command.Group
                    heading="Navigation"
                    className="[&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5 [&_[cmdk-group-heading]]:text-xs [&_[cmdk-group-heading]]:font-medium [&_[cmdk-group-heading]]:text-zinc-500"
                  >
                    <CommandItem
                      onSelect={() => handleAction(() => onSwitchView('board'))}
                      icon={<LayoutGrid className="h-4 w-4" />}
                      label="Switch to Board view"
                      shortcut={['⌘', '1']}
                    />
                    <CommandItem
                      onSelect={() => handleAction(() => onSwitchView('list'))}
                      icon={<List className="h-4 w-4" />}
                      label="Switch to List view"
                      shortcut={['⌘', '2']}
                    />
                    <CommandItem
                      onSelect={() => handleAction(() => onSwitchView('timeline'))}
                      icon={<Calendar className="h-4 w-4" />}
                      label="Switch to Timeline view"
                      shortcut={['⌘', '3']}
                    />
                    <CommandItem
                      onSelect={() => handleAction(() => console.log('Open settings'))}
                      icon={<Settings className="h-4 w-4" />}
                      label="Open settings"
                      shortcut={['⌘', ',']}
                    />
                  </Command.Group>

                  {/* Recent Tickets Group */}
                  <Command.Group
                    heading="Recent Tickets"
                    className="[&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5 [&_[cmdk-group-heading]]:text-xs [&_[cmdk-group-heading]]:font-medium [&_[cmdk-group-heading]]:text-zinc-500"
                  >
                    {RECENT_TICKETS.map((ticket) => (
                      <CommandItem
                        key={ticket.id}
                        onSelect={() => handleAction(() => console.log('Open ticket', ticket.id))}
                        icon={<Clock className="h-4 w-4" />}
                        label={ticket.title}
                        badge={
                          <span
                            className={cn(
                              'text-xs font-medium capitalize',
                              priorityColors[ticket.priority]
                            )}
                          >
                            {ticket.priority}
                          </span>
                        }
                      />
                    ))}
                  </Command.Group>
                </Command.List>
              </Command>
            </motion.div>
          </div>
        </>
      )}
    </AnimatePresence>
  );
}

// Command Item Component
interface CommandItemProps {
  onSelect: () => void;
  icon: React.ReactNode;
  label: string;
  shortcut?: string[];
  badge?: React.ReactNode;
}

function CommandItem({ onSelect, icon, label, shortcut, badge }: CommandItemProps) {
  return (
    <Command.Item
      onSelect={onSelect}
      className={cn(
        'relative flex cursor-pointer select-none items-center rounded-lg px-3 py-2.5',
        'text-sm text-zinc-300 outline-none',
        'transition-colors duration-150',
        'aria-selected:bg-bg-hover aria-selected:text-zinc-100',
        'data-[disabled]:pointer-events-none data-[disabled]:opacity-50'
      )}
    >
      <div className="mr-3 flex items-center justify-center text-zinc-400">{icon}</div>
      <span className="flex-1">{label}</span>

      {badge && <div className="mr-2">{badge}</div>}

      {shortcut && (
        <div className="ml-auto flex items-center gap-0.5">
          {shortcut.map((key, index) => (
            <kbd
              key={index}
              className={cn(
                'pointer-events-none inline-flex h-5 select-none items-center',
                'rounded border border-zinc-700 bg-bg-tertiary px-1.5',
                'font-mono text-[10px] font-medium text-zinc-400'
              )}
            >
              {key}
            </kbd>
          ))}
        </div>
      )}
    </Command.Item>
  );
}
