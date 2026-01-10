import { useEffect, useRef } from 'react';
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
import { cn } from '@/lib/utils';

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
  const inputRef = useRef<HTMLInputElement>(null);

  // Focus input when opened
  useEffect(() => {
    if (open) {
      // Small delay to ensure the element is rendered
      setTimeout(() => {
        inputRef.current?.focus();
      }, 50);
    }
  }, [open]);

  const handleAction = (action: () => void) => {
    action();
    onOpenChange(false);
  };

  if (!open) return null;

  return (
    <AnimatePresence>
      {open && (
        <div className="fixed inset-0 z-50">
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={() => onOpenChange(false)}
          />

          {/* Command Dialog Container */}
          <div
            className="absolute inset-0 flex items-start justify-center pt-[15vh] pointer-events-none"
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.96, y: -20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.96, y: -20 }}
              transition={{ duration: 0.15, ease: 'easeOut' }}
              className="w-full max-w-[560px] pointer-events-auto"
              onClick={(e) => e.stopPropagation()}
            >
              <Command
                className={cn(
                  'overflow-hidden rounded-xl border border-border',
                  'bg-bg-secondary shadow-2xl'
                )}
                loop
              >
                {/* Search Input */}
                <div className="flex items-center border-b border-border px-4">
                  <Search className="mr-3 h-4 w-4 shrink-0 text-zinc-500" />
                  <Command.Input
                    ref={inputRef}
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
                    <Command.Item
                      value="create-ticket"
                      onSelect={() => handleAction(onCreateTicket)}
                      className={cn(
                        'relative flex cursor-pointer select-none items-center rounded-lg px-3 py-2.5',
                        'text-sm text-zinc-300 outline-none',
                        'transition-colors duration-150',
                        'data-[selected=true]:bg-bg-hover data-[selected=true]:text-zinc-100',
                        'hover:bg-bg-hover hover:text-zinc-100'
                      )}
                    >
                      <Plus className="mr-3 h-4 w-4 text-zinc-400" />
                      <span className="flex-1">Create new ticket</span>
                      <Shortcut keys={['⌘', 'N']} />
                    </Command.Item>

                    <Command.Item
                      value="ai-assistant"
                      onSelect={() => handleAction(onOpenAI)}
                      className={cn(
                        'relative flex cursor-pointer select-none items-center rounded-lg px-3 py-2.5',
                        'text-sm text-zinc-300 outline-none',
                        'transition-colors duration-150',
                        'data-[selected=true]:bg-bg-hover data-[selected=true]:text-zinc-100',
                        'hover:bg-bg-hover hover:text-zinc-100'
                      )}
                    >
                      <Sparkles className="mr-3 h-4 w-4 text-indigo-400" />
                      <span className="flex-1">Ask AI assistant</span>
                      <Shortcut keys={['⌘', '⇧', 'A']} />
                    </Command.Item>

                    <Command.Item
                      value="daily-summary"
                      onSelect={() => handleAction(() => console.log('Daily summary'))}
                      className={cn(
                        'relative flex cursor-pointer select-none items-center rounded-lg px-3 py-2.5',
                        'text-sm text-zinc-300 outline-none',
                        'transition-colors duration-150',
                        'data-[selected=true]:bg-bg-hover data-[selected=true]:text-zinc-100',
                        'hover:bg-bg-hover hover:text-zinc-100'
                      )}
                    >
                      <FileText className="mr-3 h-4 w-4 text-zinc-400" />
                      <span className="flex-1">Get daily summary</span>
                      <Shortcut keys={['⌘', '⇧', 'S']} />
                    </Command.Item>
                  </Command.Group>

                  {/* Navigation Group */}
                  <Command.Group
                    heading="Navigation"
                    className="[&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5 [&_[cmdk-group-heading]]:text-xs [&_[cmdk-group-heading]]:font-medium [&_[cmdk-group-heading]]:text-zinc-500"
                  >
                    <Command.Item
                      value="board-view"
                      onSelect={() => handleAction(() => onSwitchView('board'))}
                      className={cn(
                        'relative flex cursor-pointer select-none items-center rounded-lg px-3 py-2.5',
                        'text-sm text-zinc-300 outline-none',
                        'transition-colors duration-150',
                        'data-[selected=true]:bg-bg-hover data-[selected=true]:text-zinc-100',
                        'hover:bg-bg-hover hover:text-zinc-100'
                      )}
                    >
                      <LayoutGrid className="mr-3 h-4 w-4 text-zinc-400" />
                      <span className="flex-1">Switch to Board view</span>
                      <Shortcut keys={['⌘', '1']} />
                    </Command.Item>

                    <Command.Item
                      value="list-view"
                      onSelect={() => handleAction(() => onSwitchView('list'))}
                      className={cn(
                        'relative flex cursor-pointer select-none items-center rounded-lg px-3 py-2.5',
                        'text-sm text-zinc-300 outline-none',
                        'transition-colors duration-150',
                        'data-[selected=true]:bg-bg-hover data-[selected=true]:text-zinc-100',
                        'hover:bg-bg-hover hover:text-zinc-100'
                      )}
                    >
                      <List className="mr-3 h-4 w-4 text-zinc-400" />
                      <span className="flex-1">Switch to List view</span>
                      <Shortcut keys={['⌘', '2']} />
                    </Command.Item>

                    <Command.Item
                      value="timeline-view"
                      onSelect={() => handleAction(() => onSwitchView('timeline'))}
                      className={cn(
                        'relative flex cursor-pointer select-none items-center rounded-lg px-3 py-2.5',
                        'text-sm text-zinc-300 outline-none',
                        'transition-colors duration-150',
                        'data-[selected=true]:bg-bg-hover data-[selected=true]:text-zinc-100',
                        'hover:bg-bg-hover hover:text-zinc-100'
                      )}
                    >
                      <Calendar className="mr-3 h-4 w-4 text-zinc-400" />
                      <span className="flex-1">Switch to Timeline view</span>
                      <Shortcut keys={['⌘', '3']} />
                    </Command.Item>

                    <Command.Item
                      value="settings"
                      onSelect={() => handleAction(() => console.log('Open settings'))}
                      className={cn(
                        'relative flex cursor-pointer select-none items-center rounded-lg px-3 py-2.5',
                        'text-sm text-zinc-300 outline-none',
                        'transition-colors duration-150',
                        'data-[selected=true]:bg-bg-hover data-[selected=true]:text-zinc-100',
                        'hover:bg-bg-hover hover:text-zinc-100'
                      )}
                    >
                      <Settings className="mr-3 h-4 w-4 text-zinc-400" />
                      <span className="flex-1">Open settings</span>
                      <Shortcut keys={['⌘', ',']} />
                    </Command.Item>
                  </Command.Group>

                  {/* Recent Tickets Group */}
                  <Command.Group
                    heading="Recent Tickets"
                    className="[&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5 [&_[cmdk-group-heading]]:text-xs [&_[cmdk-group-heading]]:font-medium [&_[cmdk-group-heading]]:text-zinc-500"
                  >
                    {RECENT_TICKETS.map((ticket) => (
                      <Command.Item
                        key={ticket.id}
                        value={`ticket-${ticket.id}-${ticket.title}`}
                        onSelect={() => handleAction(() => console.log('Open ticket', ticket.id))}
                        className={cn(
                          'relative flex cursor-pointer select-none items-center rounded-lg px-3 py-2.5',
                          'text-sm text-zinc-300 outline-none',
                          'transition-colors duration-150',
                          'data-[selected=true]:bg-bg-hover data-[selected=true]:text-zinc-100',
                          'hover:bg-bg-hover hover:text-zinc-100'
                        )}
                      >
                        <Clock className="mr-3 h-4 w-4 text-zinc-400" />
                        <span className="flex-1">{ticket.title}</span>
                        <span
                          className={cn(
                            'text-xs font-medium capitalize',
                            priorityColors[ticket.priority]
                          )}
                        >
                          {ticket.priority}
                        </span>
                      </Command.Item>
                    ))}
                  </Command.Group>
                </Command.List>
              </Command>
            </motion.div>
          </div>
        </div>
      )}
    </AnimatePresence>
  );
}

// Shortcut display component
function Shortcut({ keys }: { keys: string[] }) {
  return (
    <div className="ml-auto flex items-center gap-0.5">
      {keys.map((key, index) => (
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
  );
}
