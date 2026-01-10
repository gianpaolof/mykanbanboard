// components/layout/Header.example.tsx
// Example usage of the Header component

import { Header } from './Header';

export function HeaderExample() {
  return (
    <div className="min-h-screen bg-bg-primary">
      <Header
        boardTitle="My Project"
        ticketCount={24}
        lastUpdated="2m ago"
        currentView="board"
        onSearchClick={() => console.log('Open search/command palette')}
        onAIClick={() => console.log('Open AI panel')}
        onSettingsClick={() => console.log('Open settings')}
        onViewChange={(view) => console.log('View changed to:', view)}
      />

      <main className="p-6">
        <p className="text-zinc-400">
          Press ⌘K to open the command palette
        </p>
      </main>
    </div>
  );
}

// Usage in your main app:
// import { Header } from '@/components/layout';
//
// function App() {
//   const [view, setView] = useState<'board' | 'list' | 'timeline'>('board');
//
//   return (
//     <div className="min-h-screen bg-bg-primary">
//       <Header
//         boardTitle="My Kanban Board"
//         ticketCount={42}
//         lastUpdated="5m ago"
//         currentView={view}
//         onSearchClick={() => setCommandPaletteOpen(true)}
//         onAIClick={() => setAIPanelOpen(true)}
//         onSettingsClick={() => setSettingsOpen(true)}
//         onViewChange={setView}
//       />
//
//       {/* Your board content */}
//     </div>
//   );
// }
