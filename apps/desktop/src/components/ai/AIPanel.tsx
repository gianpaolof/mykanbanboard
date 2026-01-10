// components/ai/AIPanel.tsx
import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Sparkles,
  X,
  Bot,
  User,
  Target,
  ArrowUp,
  Loader2
} from 'lucide-react';
import { cn } from '../../lib/utils';
import type { Priority } from '../../types';

// ===========================================
// TYPES
// ===========================================

export interface AISuggestion {
  title: string;
  items: { priority: Priority; text: string }[];
}

export interface AIMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  suggestions?: AISuggestion[];
}

export interface AIPanelProps {
  open: boolean;
  onClose: () => void;
  messages: AIMessage[];
  onSendMessage: (message: string) => void;
  isLoading?: boolean;
}

// ===========================================
// PRIORITY DOT
// ===========================================

const PriorityDot = ({ priority }: { priority: Priority }) => {
  const colorMap: Record<Priority, string> = {
    critical: 'bg-priority-critical',
    high: 'bg-priority-high',
    medium: 'bg-priority-medium',
    low: 'bg-priority-low',
  };

  return (
    <div className={cn('w-1.5 h-1.5 rounded-full flex-shrink-0', colorMap[priority])} />
  );
};

// ===========================================
// SUGGESTION BOX
// ===========================================

const SuggestionBox = ({ suggestion }: { suggestion: AISuggestion }) => {
  return (
    <div className="mt-3 rounded-lg border border-glass-border bg-glass-bg backdrop-blur-xl p-3">
      <div className="flex items-center gap-2 mb-2">
        <Target className="w-4 h-4 text-accent" />
        <span className="text-sm font-medium text-white">{suggestion.title}</span>
      </div>
      <div className="space-y-1.5">
        {suggestion.items.map((item, idx) => (
          <div key={idx} className="flex items-start gap-2 text-sm">
            <PriorityDot priority={item.priority} />
            <span className="text-gray-300 leading-relaxed">{item.text}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

// ===========================================
// MESSAGE BUBBLE
// ===========================================

const MessageBubble = ({ message }: { message: AIMessage }) => {
  const isAssistant = message.role === 'assistant';

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className={cn(
        'flex gap-3 group',
        !isAssistant && 'flex-row-reverse'
      )}
    >
      {/* Avatar */}
      <div
        className={cn(
          'w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0',
          isAssistant
            ? 'bg-gradient-to-br from-indigo-500 to-purple-500'
            : 'bg-bg-tertiary'
        )}
      >
        {isAssistant ? (
          <Bot className="w-4 h-4 text-white" />
        ) : (
          <User className="w-4 h-4 text-gray-400" />
        )}
      </div>

      {/* Message Content */}
      <div className={cn('flex-1 min-w-0', !isAssistant && 'flex justify-end')}>
        <div
          className={cn(
            'max-w-[85%] rounded-2xl px-4 py-2.5',
            isAssistant
              ? 'bg-glass-bg border border-glass-border backdrop-blur-xl'
              : 'bg-accent text-white'
          )}
        >
          <p
            className={cn(
              'text-sm leading-relaxed whitespace-pre-wrap',
              isAssistant ? 'text-gray-100' : 'text-white'
            )}
          >
            {message.content}
          </p>

          {/* Suggestions */}
          {isAssistant && message.suggestions && message.suggestions.length > 0 && (
            <div className="space-y-2">
              {message.suggestions.map((suggestion, idx) => (
                <SuggestionBox key={idx} suggestion={suggestion} />
              ))}
            </div>
          )}
        </div>

        {/* Timestamp */}
        <div
          className={cn(
            'mt-1 px-1 text-2xs text-gray-500',
            !isAssistant && 'text-right'
          )}
        >
          {new Date(message.timestamp).toLocaleTimeString('en', {
            hour: '2-digit',
            minute: '2-digit',
          })}
        </div>
      </div>
    </motion.div>
  );
};

// ===========================================
// AI PANEL
// ===========================================

export const AIPanel = ({
  open,
  onClose,
  messages,
  onSendMessage,
  isLoading = false,
}: AIPanelProps) => {
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Focus input when panel opens
  useEffect(() => {
    if (open) {
      inputRef.current?.focus();
    }
  }, [open]);

  const handleSend = () => {
    if (!inputValue.trim() || isLoading) return;

    onSendMessage(inputValue.trim());
    setInputValue('');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
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
            transition={{ duration: 0.2 }}
            className="fixed inset-0 bg-black/20 backdrop-blur-sm z-40"
            onClick={onClose}
          />

          {/* Panel */}
          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{
              type: 'spring',
              damping: 30,
              stiffness: 300
            }}
            className="fixed right-0 top-0 bottom-0 w-[420px] bg-bg-secondary border-l border-border-subtle z-50 flex flex-col"
          >
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-border-subtle">
              <div className="flex items-center gap-2">
                <div className="p-1.5 rounded-lg bg-gradient-to-br from-indigo-500/20 to-purple-500/20">
                  <Sparkles className="w-4 h-4 text-indigo-400" />
                </div>
                <h2 className="text-base font-semibold text-white">AI Assistant</h2>
              </div>

              <button
                onClick={onClose}
                className="p-1.5 rounded-lg hover:bg-bg-hover active:bg-bg-active transition-colors"
              >
                <X className="w-4 h-4 text-gray-400" />
              </button>
            </div>

            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
              {messages.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-center">
                  <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-500/20 to-purple-500/20 flex items-center justify-center mb-4">
                    <Sparkles className="w-8 h-8 text-indigo-400" />
                  </div>
                  <h3 className="text-base font-medium text-white mb-2">
                    AI Assistant Ready
                  </h3>
                  <p className="text-sm text-gray-400 max-w-[280px]">
                    Ask me to help with triaging tickets, decomposing tasks, or
                    getting a daily summary.
                  </p>
                </div>
              ) : (
                <>
                  {messages.map((message) => (
                    <MessageBubble key={message.id} message={message} />
                  ))}
                  {isLoading && (
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="flex gap-3"
                    >
                      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center flex-shrink-0">
                        <Bot className="w-4 h-4 text-white" />
                      </div>
                      <div className="flex items-center gap-1 bg-glass-bg border border-glass-border backdrop-blur-xl rounded-2xl px-4 py-3">
                        <Loader2 className="w-4 h-4 text-indigo-400 animate-spin" />
                        <span className="text-sm text-gray-400 ml-2">Thinking...</span>
                      </div>
                    </motion.div>
                  )}
                  <div ref={messagesEndRef} />
                </>
              )}
            </div>

            {/* Input Area */}
            <div className="px-6 py-4 border-t border-border-subtle">
              <div className="flex items-end gap-2">
                <div className="flex-1 relative">
                  <input
                    ref={inputRef}
                    type="text"
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Ask AI anything..."
                    disabled={isLoading}
                    className={cn(
                      'w-full px-4 py-2.5 pr-10',
                      'bg-bg-tertiary border border-border-subtle rounded-xl',
                      'text-sm text-white placeholder:text-gray-500',
                      'focus:outline-none focus:ring-2 focus:ring-accent/50 focus:border-accent',
                      'disabled:opacity-50 disabled:cursor-not-allowed',
                      'transition-all duration-200'
                    )}
                  />
                </div>

                <button
                  onClick={handleSend}
                  disabled={!inputValue.trim() || isLoading}
                  className={cn(
                    'p-2.5 rounded-xl',
                    'bg-accent hover:bg-accent-hover active:scale-95',
                    'disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-accent',
                    'transition-all duration-200'
                  )}
                >
                  <ArrowUp className="w-5 h-5 text-white" />
                </button>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};
