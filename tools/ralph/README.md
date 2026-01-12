# Ralph Scripts per macOS

Script Ralph modificati per funzionare su macOS con Claude Code.

## Cos'è Ralph?

Ralph è un sistema di automazione per Claude Code che permette di eseguire task complessi in loop con rate limiting e documentazione automatica.

**Repository originale:** https://github.com/frankbria/ralph-claude-code

## Modifiche per macOS

Questi script sono stati modificati rispetto agli originali per funzionare correttamente su macOS:

| File | Modifica | Motivo |
|------|----------|--------|
| `ralph_loop.sh` | Aggiunto `CLAUDE_EXTRA_FLAGS="--dangerously-skip-permissions"` | Permette automazione senza prompt di conferma |
| `ralph_loop.sh` | Compatibilità `gtimeout` (linee 81-90) | macOS non ha il comando `timeout`, usa `gtimeout` da coreutils |
| `ralph_loop.sh` | Fix riferimenti tmux pane | Cambiato da `$session_name:0.X` a `${session_name}.X` |
| `ralph_loop.sh` | Reset exit signals dopo completamento | Evita false detection di completamento al prossimo run |
| `ralph_import.sh` | Aggiunto `CLAUDE_EXTRA_FLAGS` | Stessa ragione del loop |

## Requisiti macOS

```bash
# Installa coreutils per avere gtimeout
brew install coreutils

# Verifica installazione
gtimeout --version
```

## Installazione

### Opzione 1: Sostituire gli script installati

```bash
# Backup degli originali
cp ~/.ralph/ralph_loop.sh ~/.ralph/ralph_loop.sh.bak
cp ~/.ralph/ralph_import.sh ~/.ralph/ralph_import.sh.bak

# Copia i modificati
cp tools/ralph/ralph_loop.sh ~/.ralph/
cp tools/ralph/ralph_import.sh ~/.ralph/
cp tools/ralph/lib/*.sh ~/.ralph/lib/
```

### Opzione 2: Usare direttamente da questa directory

```bash
# Aggiungi al PATH (in .zshrc o .bashrc)
export PATH="$PATH:/path/to/kanban/tools/ralph"

# Oppure crea symlink
ln -sf /path/to/kanban/tools/ralph/ralph_loop.sh ~/.local/bin/ralph-loop
```

## Struttura Directory

```
tools/ralph/
├── README.md              # Questa documentazione
├── ralph_loop.sh          # Script principale (modificato)
├── ralph_import.sh        # Import PRD (modificato)
├── ralph_monitor.sh       # Monitor (non modificato)
├── setup.sh               # Setup originale
└── lib/
    ├── circuit_breaker.sh # Gestione errori e retry
    ├── date_utils.sh      # Utility date
    └── response_analyzer.sh # Analisi risposte Claude
```

## Uso

```bash
# Avvia ralph in tmux con monitor
ralph --tmux

# Avvia solo il loop
ralph

# Import di un PRD
ralph-import path/to/prd.md
```

## Differenze Chiave dagli Originali

### 1. Flag `--dangerously-skip-permissions`

Aggiunto per permettere l'esecuzione automatica senza conferme manuali. **Usare con cautela** - Claude avrà accesso completo al filesystem.

### 2. Compatibilità Timeout

```bash
# macOS compatibility: use gtimeout if timeout not available
if command -v timeout &> /dev/null; then
    TIMEOUT_CMD="timeout"
elif command -v gtimeout &> /dev/null; then
    TIMEOUT_CMD="gtimeout"
else
    TIMEOUT_CMD=""  # Fallback: no timeout
fi
```

### 3. Fix Tmux

I riferimenti ai pane tmux sono stati corretti per la sintassi macOS:
- Prima: `tmux send-keys -t "$session_name:0.1"`
- Dopo: `tmux send-keys -t "${session_name}.1"`

## Troubleshooting

### "timeout: command not found"

```bash
brew install coreutils
```

### Tmux pane non risponde

Verifica la sessione:
```bash
tmux list-sessions
tmux list-panes -t ralph
```

### Loop si blocca

Controlla i file di stato:
```bash
cat .exit_signals
cat .circuit_breaker_state
```

Reset manuale:
```bash
rm .exit_signals .circuit_breaker_state .call_count
```
