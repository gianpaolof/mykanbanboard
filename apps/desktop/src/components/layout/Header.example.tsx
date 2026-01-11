// components/layout/Header.example.tsx
// Example usage of the Header component

import { useState } from 'react';
import { Header } from './Header';
import type { FilterConfig } from '@/types';

export function HeaderExample() {
  const [filter, setFilter] = useState<FilterConfig>({});

  return (
    <div className="min-h-screen bg-bg-primary">
      <Header
        boardTitle="My Project"
        ticketCount={24}
        lastUpdated="2m ago"
        currentView="board"
        onAIClick={() => console.log('Open AI panel')}
        onSettingsClick={() => console.log('Open settings')}
        onViewChange={(view) => console.log('View changed to:', view)}
        filter={filter}
        onFilterChange={setFilter}
      />

      <main className="p-6">
        <p className="text-zinc-400">
          Use the search bar and filters in the header
        </p>
      </main>
    </div>
  );
}

// Usage in your main app:
// import { Header } from '@/components/layout';
// import type { FilterConfig } from '@/types';
//
// function App() {
//   const [view, setView] = useState<'board' | 'list' | 'timeline'>('board');
//   const [filter, setFilter] = useState<FilterConfig>({});
//
//   return (
//     <div className="min-h-screen bg-bg-primary">
//       <Header
//         boardTitle="My Kanban Board"
//         ticketCount={42}
//         lastUpdated="5m ago"
//         currentView={view}
//         onAIClick={() => setAIPanelOpen(true)}
//         onSettingsClick={() => setSettingsOpen(true)}
//         onViewChange={setView}
//         filter={filter}
//         onFilterChange={setFilter}
//       />
//
//       {/* Your board content */}
//     </div>
//   );
// }
