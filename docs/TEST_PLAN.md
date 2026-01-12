# Kanban AI - Comprehensive Manual Test Plan

> Test plan per verificare tutte le funzionalità dell'applicazione.
> Esegui ogni test e marca con [x] quando verificato.

---

## 1. Board Management

### 1.1 CRUD Board

- [ ] **Crea board**: Click "+" nella sidebar > inserisci nome > conferma
  - Expected: Nuova board appare nella sidebar
- [ ] **Rinomina board**: Click destro su board > Rinomina > nuovo nome
  - Expected: Nome aggiornato
- [ ] **Elimina board**: Click destro su board > Elimina > conferma
  - Expected: Board rimossa dalla sidebar
- [ ] **Switch board**: Click su altra board nella sidebar
  - Expected: Carica la board selezionata

### 1.2 CRUD Columns

- [ ] **Aggiungi colonna**: Usa + alla fine delle colonne
  - Expected: Nuova colonna appare
- [ ] **Rinomina colonna**: Click sul nome colonna > modifica
  - Expected: Nome aggiornato
- [ ] **Elimina colonna**: (se implementato)
  - Expected: Colonna rimossa
- [ ] **Riordina colonne**: Drag & drop header colonna
  - Expected: Colonne riordinate

### 1.3 Drag & Drop

- [ ] **Sposta ticket tra colonne**: Drag ticket da una colonna all'altra
  - Expected: Ticket appare nella nuova colonna
- [ ] **Riordina ticket nella stessa colonna**: Drag ticket sopra/sotto altro ticket
  - Expected: Ordine aggiornato
- [ ] **Drag annullato**: Inizia drag, premi ESC o rilascia fuori
  - Expected: Ticket torna alla posizione originale

---

## 2. Ticket Management

### 2.1 CRUD Ticket

- [ ] **Crea ticket**: Click "+ Add Ticket" in una colonna
  - Expected: Modal creazione si apre
- [ ] **Inserisci titolo**: Compila titolo ticket
  - Expected: Ticket creato con il titolo
- [ ] **Inserisci descrizione**: Compila campo descrizione
  - Expected: Descrizione salvata
- [ ] **Modifica ticket**: Click su ticket esistente
  - Expected: Modal dettaglio si apre
- [ ] **Salva modifiche**: Modifica campi > Save Changes
  - Expected: Modifiche persistite
- [ ] **Elimina ticket**: Click Delete nel modal
  - Expected: Ticket rimosso

### 2.2 Priority

- [ ] **Imposta priority Low**: Seleziona Low dal dropdown
  - Expected: Badge verde, priority salvata
- [ ] **Imposta priority Medium**: Seleziona Medium
  - Expected: Badge giallo
- [ ] **Imposta priority High**: Seleziona High
  - Expected: Badge arancione
- [ ] **Imposta priority Critical**: Seleziona Critical
  - Expected: Badge rosso

### 2.3 Effort

- [ ] **Imposta effort XS**: Seleziona XS (< 1 hour)
  - Expected: Badge XS verde
- [ ] **Imposta effort S**: Seleziona S (Half day)
  - Expected: Badge S blu
- [ ] **Imposta effort M**: Seleziona M (1-2 days)
  - Expected: Badge M giallo
- [ ] **Imposta effort L**: Seleziona L (3-5 days)
  - Expected: Badge L arancione
- [ ] **Imposta effort XL**: Seleziona XL (1+ week)
  - Expected: Badge XL rosso

### 2.4 Labels

- [ ] **Aggiungi label**: Click "+ Add label"
  - Expected: Label aggiunta al ticket
- [ ] **Rimuovi label**: Click su label esistente
  - Expected: Label rimossa

### 2.5 Due Date

- [ ] **Imposta due date**: Seleziona data nel calendario
  - Expected: Data mostrata sul ticket
- [ ] **Rimuovi due date**: Cancella data
  - Expected: Due date rimossa

---

## 3. Subtasks / Checklists

- [ ] **Aggiungi subtask**: Nel modal ticket, scrivi titolo subtask
  - Expected: Subtask appare nella lista
- [ ] **Completa subtask**: Click checkbox del subtask
  - Expected: Subtask marcato come completato
- [ ] **De-completa subtask**: Click checkbox di subtask completato
  - Expected: Subtask torna incompleto
- [ ] **Elimina subtask**: Click X su subtask
  - Expected: Subtask rimosso
- [ ] **Progress bar**: Completa alcuni subtask
  - Expected: Barra progresso si aggiorna

---

## 4. Views

### 4.1 Board View

- [ ] **Attiva Board view**: Click icona Board nell'header
  - Expected: Vista Kanban con colonne

### 4.2 List View

- [ ] **Attiva List view**: Click icona List nell'header
  - Expected: Toast "List view coming soon" o vista lista

### 4.3 Timeline View

- [ ] **Attiva Timeline view**: Click icona Timeline nell'header
  - Expected: Toast o vista timeline

### 4.4 Calendar View

- [ ] **Attiva Calendar view**: Click icona Calendar nell'header
  - Expected: Vista calendario con ticket con due date
- [ ] **Naviga mese**: Click frecce prev/next
  - Expected: Mese cambia
- [ ] **Oggi**: Click "Today"
  - Expected: Torna al mese corrente
- [ ] **Click su giorno con ticket**: Click sul giorno
  - Expected: Mostra ticket di quel giorno

---

## 5. AI Agent - Triage

**Prerequisiti**: Server agent attivo su localhost:8765

- [ ] **Apri AI Triage**: Nel modal ticket, click "AI Triage"
  - Expected: Loading spinner
- [ ] **Ricevi suggerimenti**: Attendi risposta
  - Expected: Mostra priority, effort, labels suggeriti
- [ ] **Applica suggerimenti**: Click "Apply Suggestions"
  - Expected: Campi aggiornati con valori suggeriti
- [ ] **Dismiss suggerimenti**: Click "Dismiss"
  - Expected: Panel suggerimenti si chiude
- [ ] **Errore triage**: Simula errore (server spento)
  - Expected: Mostra messaggio errore

---

## 6. AI Agent - Decompose

- [ ] **Click Decompose**: Nel modal ticket, click "Decompose"
  - Expected: Loading spinner
- [ ] **Visualizza subtask suggeriti**: Attendi risposta
  - Expected: Lista subtask con checkbox
- [ ] **Toggle selezione subtask**: Click su subtask
  - Expected: Subtask selezionato/deselezionato
- [ ] **Crea subtask selezionati**: Click "Create Selected (N)"
  - Expected: Subtask creati e aggiunti al ticket
- [ ] **Annulla decompose**: Click "Cancel"
  - Expected: Panel decompose si chiude

---

## 7. AI Agent - Chat

- [ ] **Apri AI Chat**: Click bottone "AI" nell'header
  - Expected: Panel chat si apre
- [ ] **Invia messaggio**: Scrivi messaggio > Enter
  - Expected: Messaggio appare, loading, risposta AI
- [ ] **Chiudi chat**: Click X
  - Expected: Panel si chiude
- [ ] **Escape chiude chat**: Premi ESC
  - Expected: Panel si chiude

---

## 8. AI Agent - Semantic Search

- [ ] **Usa search bar**: Scrivi keyword nella search bar
  - Expected: Ticket filtrati o risultati semantic search
- [ ] **Risultati vuoti**: Cerca termine non presente
  - Expected: "No results" o lista vuota

---

## 9. AI Agent - Daily Summary

- [ ] **Richiedi daily summary**: ⌘⇧D o via command palette
  - Expected: Toast o panel con summary del giorno

---

## 10. AI Agent - Parse Rule (Automation)

- [ ] **Crea regola naturale**: "Quando un ticket diventa critical, avvisami"
  - Expected: Regola parsata e salvata

---

## 11. AI Agent - Judge (Quality Check)

**Endpoint**: POST /api/agent/judge

- [ ] **Click Quality badge**: Nel modal ticket, click badge "Quality"
  - Expected: Popover con loading
- [ ] **Visualizza scores**: Attendi risposta
  - Expected: Clarity, Completeness, Actionability scores (0-10)
- [ ] **Visualizza overall score**:
  - Expected: Score medio con colore (verde >7, giallo 5-7, rosso <5)
- [ ] **Visualizza feedback**:
  - Expected: Suggerimenti miglioramento
- [ ] **Refresh score**: Click "Refresh Score"
  - Expected: Nuova analisi

---

## 12. AI Agent - Deep Analyze (Multi-hop)

**Endpoint**: POST /api/agent/analyze

- [ ] **Click Deep Analyze**: Nel modal ticket, click "Deep Analyze"
  - Expected: Panel espandibile con loading skeleton
- [ ] **Context Summary**: Attendi risposta
  - Expected: Mostra context summary
- [ ] **Patterns**:
  - Expected: Chip/tags con pattern identificati
- [ ] **Insights**:
  - Expected: Lista insights
- [ ] **Recommendations**:
  - Expected: Sezione recommendations espandibile
- [ ] **Complexity badge**:
  - Expected: Low/Medium/High con colore
- [ ] **Chiudi panel**: Click X o "Deep Analyze" di nuovo
  - Expected: Panel si chiude

---

## 13. AI Agent - Stats Dashboard

**Endpoint**: GET /api/agent/stats

- [ ] **Apri Stats panel**: Click icona grafico nell'header
  - Expected: Panel stats si apre
- [ ] **Visualizza Total Calls**:
  - Expected: Numero chiamate nel periodo
- [ ] **Visualizza Avg Latency**:
  - Expected: Latenza media in ms
- [ ] **Visualizza Success Rate**:
  - Expected: Percentuale successo
- [ ] **Visualizza Total Tokens**:
  - Expected: Token utilizzati
- [ ] **Cambia periodo a 1h**: Click "1h"
  - Expected: Stats aggiornate per ultima ora
- [ ] **Cambia periodo a 24h**: Click "24h"
  - Expected: Stats aggiornate per ultimo giorno
- [ ] **Cambia periodo a 7d**: Click "7d"
  - Expected: Stats aggiornate per ultima settimana
- [ ] **Refresh manuale**: Click icona refresh
  - Expected: Dati aggiornati
- [ ] **Chiudi panel**: Click X
  - Expected: Panel si chiude

---

## 14. AI Agent - Suggestions

**Endpoint**: POST /api/agent/suggestions

- [ ] **Widget suggestions visibile**: In sidebar o layout
  - Expected: Widget con lista suggestions
- [ ] **Vedi high priority suggestions**:
  - Expected: Badge rosso per high priority
- [ ] **Dismiss suggestion**: Click X su suggestion
  - Expected: Suggestion rimossa dalla lista
- [ ] **Refresh suggestions**: Click refresh
  - Expected: Lista aggiornata
- [ ] **Collapse/Expand**: Click header widget
  - Expected: Widget si espande/collassa

---

## 15. Automation Rules

- [ ] **Apri panel automation**: Via settings o command palette
  - Expected: Panel regole si apre
- [ ] **Crea regola manuale**: Aggiungi trigger e action
  - Expected: Regola creata
- [ ] **Attiva regola**: Toggle attivo
  - Expected: Regola attiva
- [ ] **Disattiva regola**: Toggle off
  - Expected: Regola disattivata
- [ ] **Elimina regola**: Click delete
  - Expected: Regola rimossa

---

## 16. Command Palette

- [ ] **Apri con ⌘K**: Premi ⌘K (Cmd+K)
  - Expected: Command palette si apre
- [ ] **Cerca comando**: Scrivi "new"
  - Expected: Mostra "New Ticket" e altri match
- [ ] **Esegui comando**: Seleziona e Enter
  - Expected: Azione eseguita
- [ ] **Chiudi con ESC**: Premi ESC
  - Expected: Palette si chiude
- [ ] **Chiudi click fuori**: Click fuori dalla palette
  - Expected: Palette si chiude

---

## 17. Keyboard Shortcuts

| Shortcut | Azione | Status |
|----------|--------|--------|
| ⌘K | Apri command palette | [ ] |
| ⌘N | Nuovo ticket | [ ] |
| ⌘⇧A | Apri AI chat | [ ] |
| ⌘/ | Toggle sidebar | [ ] |
| ⌘1 | Board view | [ ] |
| ⌘2 | List view | [ ] |
| ⌘3 | Timeline view | [ ] |
| ⌘4 | Calendar view | [ ] |
| ⌘, | Apri settings | [ ] |
| ESC | Chiudi modali | [ ] |

---

## 18. Settings

- [ ] **Apri settings**: ⌘, o click icona ingranaggio
  - Expected: Modal settings si apre
- [ ] **Theme toggle**: Cambia tema light/dark
  - Expected: Tema cambia
- [ ] **AI Settings**: Configura API
  - Expected: Settings salvate
- [ ] **Keyboard shortcuts**: Visualizza shortcuts
  - Expected: Lista shortcuts
- [ ] **Chiudi settings**: Click X o ESC
  - Expected: Modal si chiude

---

## 19. Error Handling

- [ ] **Server agent non disponibile**: Ferma server agent
  - Expected: Messaggi errore chiari, retry button
- [ ] **Network error**: Disconnetti network
  - Expected: Errore gestito gracefully
- [ ] **Timeout**: Operazione lunga
  - Expected: Loading visibile, timeout gestito

---

## 20. Performance

- [ ] **Caricamento board**: Board con 50+ ticket
  - Expected: Carica in < 2 secondi
- [ ] **Drag & drop fluido**: Con molti ticket
  - Expected: 60fps, nessun lag
- [ ] **AI response time**: Chiamate agent
  - Expected: Latenza < 15 secondi per operazioni normali

---

## Note di Test

### Setup Ambiente Test

1. Avvia Tauri dev: `cd apps/desktop && pnpm tauri dev`
2. Avvia Agent server: `cd services/agent && uv run fastapi dev`
3. Verifica connessione: `curl http://localhost:8765/health`

### Ambiente

- OS: macOS / Windows / Linux
- Data test: _______________
- Tester: _______________

### Bugs Trovati

| ID | Descrizione | Gravità | Status |
|----|-------------|---------|--------|
| | | | |
| | | | |
| | | | |

---

*Ultimo aggiornamento: 2024-01-11*
