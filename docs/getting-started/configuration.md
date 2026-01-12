# Configuration

Questa guida spiega come configurare Kanban AI per le tue esigenze.

## Configurazione Agent AI

L'agent AI si configura tramite variabili d'ambiente in `services/agent/.env`.

### File .env

Crea il file partendo dal template:

```bash
cd services/agent
cp .env.example .env
```

### Variabili Disponibili

#### LLM Provider

```env
# Provider da usare: "anthropic" o "openai"
LLM_PROVIDER=anthropic

# Modello principale
DEFAULT_MODEL=claude-sonnet-4-20250514

# Modello di fallback
FALLBACK_MODEL=gpt-4o-mini
```

#### API Keys

```env
# Anthropic (Claude)
ANTHROPIC_API_KEY=sk-ant-api03-...

# OpenAI (GPT)
OPENAI_API_KEY=sk-...
```

!!! warning "Sicurezza"
    Non committare mai il file `.env` nel repository. E gia in `.gitignore`.

#### Server

```env
# Host e porta del server agent
HOST=127.0.0.1
PORT=8765

# Abilita debug mode (piu log, reload automatico)
DEBUG=false
```

#### Embedding

```env
# Modello per generare embeddings (ricerca semantica)
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSIONS=1536
```

#### ChromaDB (Vector Store)

```env
# Path per il database vettoriale
CHROMA_PATH=./data/chroma
CHROMA_COLLECTION=tickets
```

#### Behavior

```env
# Abilita auto-triage sui nuovi ticket
AUTO_TRIAGE_ENABLED=true

# Numero massimo di subtask nella decomposizione
MAX_DECOMPOSE_SUBTASKS=7

# Limite risultati ricerca
SEARCH_RESULTS_LIMIT=10

# Rate limiting (richieste al minuto)
MAX_REQUESTS_PER_MINUTE=20
```

### Configurazione Completa

Esempio di `.env` completo:

```env
# === LLM Configuration ===
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx
OPENAI_API_KEY=sk-xxxxx
DEFAULT_MODEL=claude-sonnet-4-20250514
FALLBACK_MODEL=gpt-4o-mini

# === Embedding ===
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSIONS=1536

# === Database ===
CHROMA_PATH=./data/chroma
CHROMA_COLLECTION=tickets

# === Server ===
HOST=127.0.0.1
PORT=8765
DEBUG=false

# === Behavior ===
AUTO_TRIAGE_ENABLED=true
MAX_DECOMPOSE_SUBTASKS=7
SEARCH_RESULTS_LIMIT=10
MAX_REQUESTS_PER_MINUTE=20
```

## Configurazione Frontend

### Tailwind CSS

Il tema si configura in `apps/desktop/tailwind.config.js`:

```javascript
module.exports = {
  theme: {
    extend: {
      colors: {
        // Background colors
        background: '#0a0a0b',
        surface: '#141415',

        // Text colors
        foreground: '#fafafa',
        muted: '#a1a1aa',

        // Accent colors
        primary: '#6366f1',    // Indigo
        success: '#22c55e',
        warning: '#eab308',
        destructive: '#ef4444',
      },
    },
  },
}
```

### Shortcuts Personalizzati

I keyboard shortcuts sono definiti in `apps/desktop/src/lib/shortcuts.ts`:

```typescript
export const shortcuts = {
  commandPalette: ['Meta+k', 'Ctrl+k'],
  newTicket: ['Meta+n', 'Ctrl+n'],
  aiChat: ['Meta+Shift+a', 'Ctrl+Shift+a'],
  toggleSidebar: ['Meta+/', 'Ctrl+/'],
  // ... altri shortcuts
}
```

## Configurazione Tauri

### App Metadata

In `apps/desktop/src-tauri/tauri.conf.json`:

```json
{
  "productName": "Kanban AI",
  "version": "0.1.0",
  "identifier": "com.kanban-ai.app",
  "build": {
    "beforeBuildCommand": "pnpm build",
    "beforeDevCommand": "pnpm dev",
    "frontendDist": "../dist",
    "devUrl": "http://localhost:5173"
  }
}
```

### Window Settings

```json
{
  "app": {
    "windows": [
      {
        "title": "Kanban AI",
        "width": 1200,
        "height": 800,
        "minWidth": 800,
        "minHeight": 600,
        "resizable": true,
        "fullscreen": false,
        "decorations": true,
        "transparent": false
      }
    ]
  }
}
```

## Provider LLM

### Anthropic (Claude)

Claude e il provider consigliato per la migliore qualita.

**Modelli disponibili:**

| Modello | Uso Consigliato |
|---------|-----------------|
| `claude-sonnet-4-20250514` | Default, bilanciato |
| `claude-opus-4-20250514` | Massima qualita |
| `claude-3-5-haiku-latest` | Velocita, costi bassi |

**Configurazione:**

```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx
DEFAULT_MODEL=claude-sonnet-4-20250514
```

### OpenAI (GPT)

Alternativa valida, specialmente per embedding.

**Modelli disponibili:**

| Modello | Uso Consigliato |
|---------|-----------------|
| `gpt-4o` | Alta qualita |
| `gpt-4o-mini` | Default, economico |
| `gpt-4-turbo` | Legacy |

**Configurazione:**

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-xxxxx
DEFAULT_MODEL=gpt-4o-mini
```

## Ottimizzazione Performance

### Per Velocita

```env
# Usa modelli veloci
DEFAULT_MODEL=claude-3-5-haiku-latest
# oppure
DEFAULT_MODEL=gpt-4o-mini

# Limita risultati ricerca
SEARCH_RESULTS_LIMIT=5

# Limita subtask
MAX_DECOMPOSE_SUBTASKS=5
```

### Per Qualita

```env
# Usa modelli potenti
DEFAULT_MODEL=claude-opus-4-20250514
# oppure
DEFAULT_MODEL=gpt-4o

# Piu risultati ricerca
SEARCH_RESULTS_LIMIT=20

# Piu subtask possibili
MAX_DECOMPOSE_SUBTASKS=10
```

### Per Costi Ridotti

```env
# Modelli economici
DEFAULT_MODEL=gpt-4o-mini
FALLBACK_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small

# Limita rate
MAX_REQUESTS_PER_MINUTE=10
```

## Troubleshooting

### L'agent non risponde

1. Verifica che l'agent sia in esecuzione:
   ```bash
   curl http://localhost:8765/health
   ```

2. Controlla i log:
   ```bash
   cd services/agent
   DEBUG=true uv run fastapi dev
   ```

3. Verifica le API keys:
   ```bash
   echo $ANTHROPIC_API_KEY  # Deve mostrare la chiave
   ```

### Errori di Rate Limiting

Aumenta il limite o riduci la frequenza:

```env
MAX_REQUESTS_PER_MINUTE=30
```

### ChromaDB Corrotto

Resetta il database:

```bash
rm -rf services/agent/data/chroma
# Riavvia l'agent
```

## Prossimi Passi

- [Quick Start](quick-start.md) - Inizia ad usare l'app
- [AI Features](../user-guide/ai-features.md) - Funzionalita AI avanzate
