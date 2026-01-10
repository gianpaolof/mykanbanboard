import { useState, useRef, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  X,
  Bot,
  User,
  Send,
  Loader2,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  Plus,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { api } from '@/lib/tauri';
import type { AgentChatResult } from '@/lib/tauri';
import { useBoardStore } from '@/stores/boardStore';

// ===========================================
// TYPES
// ===========================================

export interface AgentChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  actions?: Array<{
    type: string;
    data: Record<string, unknown>;
  }>;
}

export interface AgentChatProps {
  isOpen: boolean;
  onClose: () => void;
  context?: {
    ticketId?: string;
    ticketTitle?: string;
  };
}

// ===========================================
// HELPER FUNCTIONS
// ===========================================

const formatTimestamp = (timestamp: string): string => {
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);

  if (diffMins < 1) return 'just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
  return date.toLocaleDateString('en', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

const generateMessageId = (): string => {
  return `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
};

// ===========================================
// ACTION DISPLAY
// ===========================================

interface ActionDisplayProps {
  actions: Array<{
    type: string;
    data: Record<string, unknown>;
  }>;
}

const ActionDisplay = ({ actions }: ActionDisplayProps) => {
  if (!actions || actions.length === 0) return null;

  return (
    <div className="mt-3 space-y-2">
      {actions.map((action, idx) => (
        <div
          key={idx}
          className="flex items-start gap-2 rounded-lg border border-glass-border bg-glass-bg/50 backdrop-blur-sm px-3 py-2"
        >
          <CheckCircle2 className="w-4 h-4 text-status-success mt-0.5 flex-shrink-0" />
          <div className="flex-1 min-w-0">
            <p className="text-xs font-medium text-gray-200 capitalize">
              {action.type.replace(/_/g, ' ')}
            </p>
            {Object.keys(action.data).length > 0 && (
              <p className="text-xs text-gray-400 mt-0.5 truncate">
                {JSON.stringify(action.data, null, 2)
                  .replace(/[{}"]/g, '')
                  .trim()}
              </p>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};

// ===========================================
// MESSAGE BUBBLE
// ===========================================

interface MessageBubbleProps {
  message: AgentChatMessage;
}

const MessageBubble = ({ message }: MessageBubbleProps) => {
  const isAssistant = message.role === 'assistant';

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className={cn('flex gap-3 group', !isAssistant && 'flex-row-reverse')}
    >
      {/* Avatar */}
      <div
        className={cn(
          'w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0',
          isAssistant
            ? 'bg-gradient-to-br from-indigo-500 to-purple-500'
            : 'bg-bg-tertiary border border-border-subtle'
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
              : 'bg-indigo-600/80 backdrop-blur-sm'
          )}
        >
          <p
            className={cn(
              'text-sm leading-relaxed whitespace-pre-wrap break-words',
              isAssistant ? 'text-gray-100' : 'text-white'
            )}
          >
            {message.content}
          </p>

          {/* Actions */}
          {isAssistant && message.actions && (
            <ActionDisplay actions={message.actions} />
          )}
        </div>

        {/* Timestamp */}
        <div
          className={cn(
            'mt-1 px-1 text-2xs text-gray-500',
            !isAssistant && 'text-right'
          )}
        >
          {formatTimestamp(message.timestamp)}
        </div>
      </div>
    </motion.div>
  );
};

// ===========================================
// TYPING INDICATOR
// ===========================================

const TypingIndicator = () => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="flex gap-3"
    >
      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center flex-shrink-0">
        <Bot className="w-4 h-4 text-white" />
      </div>
      <div className="flex items-center gap-1.5 bg-glass-bg border border-glass-border backdrop-blur-xl rounded-2xl px-4 py-3">
        <div className="flex gap-1">
          <div
            className="w-2 h-2 rounded-full bg-indigo-400 animate-bounce"
            style={{ animationDelay: '0ms', animationDuration: '1000ms' }}
          />
          <div
            className="w-2 h-2 rounded-full bg-indigo-400 animate-bounce"
            style={{ animationDelay: '150ms', animationDuration: '1000ms' }}
          />
          <div
            className="w-2 h-2 rounded-full bg-indigo-400 animate-bounce"
            style={{ animationDelay: '300ms', animationDuration: '1000ms' }}
          />
        </div>
        <span className="text-sm text-gray-400 ml-1">Thinking...</span>
      </div>
    </motion.div>
  );
};

// ===========================================
// AGENT CHAT COMPONENT
// ===========================================

export const AgentChat = ({ isOpen, onClose, context }: AgentChatProps) => {
  const [messages, setMessages] = useState<AgentChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Get store actions for executing agent commands
  const { addTicket, columns } = useBoardStore();

  // Execute actions returned by the agent
  const executeAction = useCallback(async (action: string, params: Record<string, unknown>): Promise<{ type: string; data: Record<string, unknown> } | null> => {
    try {
      switch (action) {
        case 'create':
        case 'create_ticket': {
          // Get first column as default if not specified
          const targetColumnId = (params.columnId as string) || columns[0]?.id;
          if (!targetColumnId) {
            throw new Error('No columns available to create ticket');
          }

          // Map priority from agent response to valid values
          const priorityMap: Record<string, 'urgent' | 'high' | 'medium' | 'low' | 'none'> = {
            'critical': 'urgent',
            'urgent': 'urgent',
            'high': 'high',
            'medium': 'medium',
            'normal': 'medium',
            'low': 'low',
            'none': 'none',
          };
          const rawPriority = (params.priority as string)?.toLowerCase() || 'medium';
          const priority = priorityMap[rawPriority] || 'medium';

          // Map effort from agent response to valid values
          const effortMap: Record<string, 'xs' | 's' | 'm' | 'l' | 'xl'> = {
            'xs': 'xs', 'extra-small': 'xs', '1': 'xs',
            's': 's', 'small': 's', '2': 's',
            'm': 'm', 'medium': 'm', '3': 'm',
            'l': 'l', 'large': 'l', '4': 'l',
            'xl': 'xl', 'extra-large': 'xl', '5': 'xl',
          };
          const rawEffort = String(params.effort || 'm').toLowerCase();
          const effort = effortMap[rawEffort] || 'm';

          const newTicket = await addTicket({
            title: (params.title as string) || 'New Ticket',
            description: (params.description as string) || '',
            columnId: targetColumnId,
            priority,
            effort,
          });

          return {
            type: 'create_ticket',
            data: { id: newTicket.id, title: newTicket.title },
          };
        }

        case 'none':
        case 'chat':
          // No action to execute, just conversation
          return null;

        default:
          console.warn(`Unknown action: ${action}`);
          return null;
      }
    } catch (err) {
      console.error('Failed to execute action:', err);
      throw err;
    }
  }, [addTicket, columns]);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  // Focus textarea when panel opens
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => {
        textareaRef.current?.focus();
      }, 100);
    }
  }, [isOpen]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(
        textareaRef.current.scrollHeight,
        200
      )}px`;
    }
  }, [inputValue]);

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: AgentChatMessage = {
      id: generateMessageId(),
      role: 'user',
      content: inputValue.trim(),
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);
    setError(null);

    try {
      // Build context object
      const chatContext = context
        ? {
            ticket_id: context.ticketId,
            ticket_title: context.ticketTitle,
          }
        : undefined;

      // Call agent API
      console.log('Calling agent API with:', userMessage.content);
      const result: AgentChatResult = await api.agent.chat(
        userMessage.content,
        chatContext
      );
      console.log('Agent API response:', result);

      // Execute action if present
      const executedActions: Array<{ type: string; data: Record<string, unknown> }> = [];

      console.log('Action from agent:', result.action, 'Params:', result.params);
      if (result.action && result.action !== 'none' && result.action !== 'chat') {
        try {
          console.log('Executing action:', result.action);
          const actionResult = await executeAction(result.action, result.params || {});
          console.log('Action result:', actionResult);
          if (actionResult) {
            executedActions.push(actionResult);
          }
        } catch (actionErr) {
          console.error('Action execution failed:', actionErr);
          // Still show the response, but note the action failed
        }
      }

      const assistantMessage: AgentChatMessage = {
        id: generateMessageId(),
        role: 'assistant',
        content: result.response,
        timestamp: new Date().toISOString(),
        actions: executedActions.length > 0 ? executedActions : result.actions,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      console.error('Agent chat error:', err);
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);

      // Add error message to chat
      const errorMsg: AgentChatMessage = {
        id: generateMessageId(),
        role: 'assistant',
        content: `Sorry, I encountered an error: ${errorMessage}`,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleClearChat = () => {
    setMessages([]);
    setError(null);
  };

  return (
    <AnimatePresence>
      {isOpen && (
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
              stiffness: 300,
            }}
            className="fixed right-0 top-0 bottom-0 w-[480px] bg-bg-secondary/95 border-l border-border-subtle backdrop-blur-xl z-50 flex flex-col"
          >
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-border-subtle flex-shrink-0">
              <div className="flex items-center gap-3">
                <div className="p-1.5 rounded-lg bg-gradient-to-br from-indigo-500/20 to-purple-500/20">
                  <Sparkles className="w-4 h-4 text-indigo-400" />
                </div>
                <div className="flex-1 min-w-0">
                  <h2 className="text-base font-semibold text-white">
                    AI Agent Chat
                  </h2>
                  {context?.ticketTitle && (
                    <p className="text-xs text-gray-400 truncate">
                      Context: {context.ticketTitle}
                    </p>
                  )}
                </div>
              </div>

              <div className="flex items-center gap-1">
                {messages.length > 0 && (
                  <button
                    onClick={handleClearChat}
                    className="px-2 py-1 text-xs text-gray-400 hover:text-gray-200 hover:bg-bg-hover rounded-lg transition-colors"
                  >
                    Clear
                  </button>
                )}
                <button
                  onClick={onClose}
                  className="p-1.5 rounded-lg hover:bg-bg-hover active:bg-bg-active transition-colors"
                >
                  <X className="w-4 h-4 text-gray-400" />
                </button>
              </div>
            </div>

            {/* Error Banner */}
            {error && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="mx-6 mt-4 px-3 py-2 bg-status-error/10 border border-status-error/20 rounded-lg flex items-start gap-2"
              >
                <AlertCircle className="w-4 h-4 text-status-error mt-0.5 flex-shrink-0" />
                <p className="text-xs text-status-error flex-1">{error}</p>
                <button
                  onClick={() => setError(null)}
                  className="text-status-error hover:text-status-error/80"
                >
                  <X className="w-3 h-3" />
                </button>
              </motion.div>
            )}

            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4 min-h-0">
              {messages.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-center">
                  <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-500/20 to-purple-500/20 flex items-center justify-center mb-4">
                    <Sparkles className="w-8 h-8 text-indigo-400" />
                  </div>
                  <h3 className="text-base font-medium text-white mb-2">
                    Start a conversation
                  </h3>
                  <p className="text-sm text-gray-400 max-w-[320px]">
                    Ask me to help with triaging tickets, decomposing tasks,
                    searching for similar tickets, or getting a daily summary.
                  </p>
                  {context?.ticketTitle && (
                    <div className="mt-4 px-3 py-2 bg-accent-muted rounded-lg">
                      <p className="text-xs text-gray-300">
                        I have context about:{' '}
                        <span className="text-white font-medium">
                          {context.ticketTitle}
                        </span>
                      </p>
                    </div>
                  )}
                </div>
              ) : (
                <>
                  {messages.map((message) => (
                    <MessageBubble key={message.id} message={message} />
                  ))}
                  <AnimatePresence>
                    {isLoading && <TypingIndicator />}
                  </AnimatePresence>
                  <div ref={messagesEndRef} />
                </>
              )}
            </div>

            {/* Input Area */}
            <div className="px-6 py-4 border-t border-border-subtle flex-shrink-0">
              <div className="flex items-end gap-2">
                <div className="flex-1 relative">
                  <textarea
                    ref={textareaRef}
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Ask AI anything... (Shift+Enter for newline)"
                    disabled={isLoading}
                    rows={1}
                    className={cn(
                      'w-full px-4 py-2.5 resize-none',
                      'bg-bg-tertiary border border-border-subtle rounded-xl',
                      'text-sm text-white placeholder:text-gray-500',
                      'focus:outline-none focus:ring-2 focus:ring-accent/50 focus:border-accent',
                      'disabled:opacity-50 disabled:cursor-not-allowed',
                      'transition-all duration-200',
                      'min-h-[44px] max-h-[200px]'
                    )}
                    style={{
                      scrollbarWidth: 'thin',
                      scrollbarColor: 'rgba(255,255,255,0.1) transparent',
                    }}
                  />
                </div>

                <button
                  onClick={handleSendMessage}
                  disabled={!inputValue.trim() || isLoading}
                  className={cn(
                    'p-2.5 rounded-xl flex-shrink-0',
                    'bg-accent hover:bg-accent-hover active:scale-95',
                    'disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-accent',
                    'transition-all duration-200'
                  )}
                  title="Send message (Enter)"
                >
                  {isLoading ? (
                    <Loader2 className="w-5 h-5 text-white animate-spin" />
                  ) : (
                    <Send className="w-5 h-5 text-white" />
                  )}
                </button>
              </div>

              <p className="text-2xs text-gray-500 mt-2">
                Press Enter to send, Shift+Enter for newline
              </p>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};
