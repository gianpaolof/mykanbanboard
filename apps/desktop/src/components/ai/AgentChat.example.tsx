/**
 * AgentChat - Example Usage
 *
 * This file demonstrates how to integrate the AgentChat component
 * into your application.
 */

import { useState } from 'react';
import { AgentChat } from './AgentChat';

export function AgentChatExample() {
  const [isOpen, setIsOpen] = useState(false);

  // Example 1: Basic usage without context
  return (
    <div>
      <button onClick={() => setIsOpen(true)}>
        Open AI Chat
      </button>

      <AgentChat
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
      />
    </div>
  );
}

// Example 2: With ticket context
export function AgentChatWithContext() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div>
      <button onClick={() => setIsOpen(true)}>
        Ask AI about this ticket
      </button>

      <AgentChat
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        context={{
          ticketId: 'ticket-123',
          ticketTitle: 'Implement authentication flow',
        }}
      />
    </div>
  );
}

// Example 3: Integration with keyboard shortcut
export function AgentChatWithShortcut() {
  const [isOpen, setIsOpen] = useState(false);

  // Add keyboard shortcut (Cmd/Ctrl + Shift + A)
  useState(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key === 'a') {
        e.preventDefault();
        setIsOpen(true);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  });

  return (
    <AgentChat
      isOpen={isOpen}
      onClose={() => setIsOpen(false)}
    />
  );
}

// Example 4: Multiple instances with different contexts
export function MultipleAgentChats() {
  const [generalChatOpen, setGeneralChatOpen] = useState(false);
  const [ticketChatOpen, setTicketChatOpen] = useState(false);

  const currentTicket = {
    id: 'ticket-456',
    title: 'Fix navigation bug',
  };

  return (
    <div>
      {/* General chat button */}
      <button onClick={() => setGeneralChatOpen(true)}>
        General AI Chat
      </button>

      {/* Ticket-specific chat button */}
      <button onClick={() => setTicketChatOpen(true)}>
        Ask about this ticket
      </button>

      {/* General chat */}
      <AgentChat
        isOpen={generalChatOpen}
        onClose={() => setGeneralChatOpen(false)}
      />

      {/* Ticket-specific chat */}
      <AgentChat
        isOpen={ticketChatOpen}
        onClose={() => setTicketChatOpen(false)}
        context={{
          ticketId: currentTicket.id,
          ticketTitle: currentTicket.title,
        }}
      />
    </div>
  );
}
