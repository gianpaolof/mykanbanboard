# Quick Start

Questa guida ti mostra come iniziare ad usare Kanban AI in pochi minuti.

## Avvio dell'Applicazione

### 1. Avvia l'Agent AI (terminale 1)

```bash
cd services/agent
uv run fastapi dev
```

Dovresti vedere:

```
INFO:     Uvicorn running on http://127.0.0.1:8765
INFO:     Started reloader process
INFO:     DSPy initialized successfully
```

### 2. Avvia l'App Desktop (terminale 2)

```bash
cd apps/desktop
pnpm tauri dev
```

L'applicazione si aprira automaticamente.

## Panoramica dell'Interfaccia

```
┌─────────────────────────────────────────────────────────────┐
│  ┌─────┐                                    [⌘K] [👤]       │
│  │ ≡   │  Kanban AI                                         │
│  └─────┘                                                    │
├─────────┬───────────────────────────────────────────────────┤
│         │                                                   │
│ Inbox   │  ┌─────────┐  ┌─────────┐  ┌─────────┐           │
│ Today   │  │  Todo   │  │In Prog. │  │  Done   │           │
│ ----    │  │         │  │         │  │         │           │
│ Board   │  │ [Card]  │  │ [Card]  │  │ [Card]  │           │
│ List    │  │ [Card]  │  │         │  │         │           │
│ Timeline│  │         │  │         │  │         │           │
│         │  └─────────┘  └─────────┘  └─────────┘           │
│         │                                                   │
├─────────┴───────────────────────────────────────────────────┤
│  [💬 Ask AI...]                                             │
└─────────────────────────────────────────────────────────────┘
```

### Elementi Principali

| Elemento | Descrizione |
|----------|-------------|
| **Sidebar** | Navigazione tra viste e filtri |
| **Board** | Colonne con ticket trascinabili |
| **Command Palette** | Accesso rapido con `Cmd+K` |
| **AI Chat** | Interazione con l'agent |

## Creare il Primo Ticket

### Metodo 1: Command Palette

1. Premi `Cmd+N` (o `Ctrl+N` su Windows/Linux)
2. Inserisci il titolo del ticket
3. Premi `Enter`

### Metodo 2: Bottone +

1. Clicca il bottone `+` in una colonna
2. Compila il form
3. Clicca "Create"

### Metodo 3: AI Chat

1. Clicca sulla chat AI in basso
2. Scrivi: "Crea un ticket per aggiungere dark mode"
3. L'agent crea il ticket con metadata suggeriti

## Auto-Triage

Quando crei un ticket, l'AI lo analizza automaticamente:

```
Titolo: Fix login bug on mobile Safari
Descrizione: Users can't login on iOS Safari

         ↓ AI Analysis ↓

Priority: high (login e critico per gli utenti)
Labels: [bug, auth, mobile]
Effort: s (1-4 ore stimate)
```

Puoi accettare o modificare i suggerimenti.

## Spostare i Ticket

### Drag & Drop

Trascina un ticket da una colonna all'altra.

### Keyboard

1. Seleziona il ticket con le frecce
2. Premi `M` per il menu "Move"
3. Scegli la destinazione

### AI Chat

Scrivi: "Sposta il bug del login in Done"

## Usare l'AI Agent

### Comandi Comuni

| Comando | Esempio |
|---------|---------|
| Crea ticket | "Crea un ticket per refactorare il modulo auth" |
| Sposta ticket | "Sposta il task di dark mode in progress" |
| Cerca | "Trova tutti i bug critici" |
| Summary | "Cosa devo fare oggi?" |
| Decompose | "Scomponi il ticket di autenticazione" |

### Esempio: Daily Summary

```
Tu: Cosa devo fare oggi?

AI: Buongiorno! Ecco il tuo focus per oggi:

📌 Priorita:
1. Fix login bug on Safari (high, in progress)
2. Prepare v2.0 release (due domani)

⚠️ Blockers:
- Payment integration attende API keys

✅ Quick wins:
- Chiudi "Update docs" - manca solo review
```

### Esempio: Task Decomposition

```
Tu: Scomponi il ticket "Implement user settings"

AI: Ho analizzato il task e suggerisco questi subtask:

1. Setup page layout (xs)
   Crea struttura base della pagina settings

2. Profile section (s)
   Form per nome, email, avatar

3. Password change (s)
   Current password + new password flow

4. Notification preferences (xs)
   Toggle per email/push notifications

5. Theme selector (xs)
   Light/dark mode switch

Vuoi che li crei come subtask?
```

## Keyboard Shortcuts

| Shortcut | Azione |
|----------|--------|
| `Cmd+K` | Command Palette |
| `Cmd+N` | Nuovo ticket |
| `Cmd+Shift+A` | Apri AI chat |
| `Cmd+/` | Toggle sidebar |
| `Cmd+1` | Vista Board |
| `Cmd+2` | Vista List |
| `Cmd+3` | Vista Timeline |
| `Cmd+4` | Vista Calendar |
| `Esc` | Chiudi modal/dialog |
| `?` | Mostra shortcuts |

## Filtri e Ricerca

### Quick Filters (Sidebar)

- **Inbox**: Ticket non triaged
- **Today**: Due oggi o in ritardo
- **All**: Tutti i ticket

### Search (Cmd+K)

```
bug           → Cerca "bug" nel titolo/descrizione
label:urgent  → Filtra per label
priority:high → Filtra per priority
@me           → Assegnati a te
```

### AI Search

```
Tu: Trova i ticket relativi a performance

AI: Ho trovato 3 ticket correlati:
1. "Optimize database queries" (85% match)
2. "Add caching layer" (72% match)
3. "Profile slow endpoints" (68% match)
```

## Prossimi Passi

- [Configuration](configuration.md) - Personalizza l'app
- [AI Features](../user-guide/ai-features.md) - Approfondisci le funzionalita AI
- [Keyboard Shortcuts](../user-guide/keyboard-shortcuts.md) - Lista completa shortcuts
