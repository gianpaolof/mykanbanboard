# Installation

Questa guida spiega come installare Kanban AI su diversi sistemi operativi.

## Requisiti di Sistema

### Hardware

- **CPU**: Qualsiasi processore moderno (Intel/AMD/Apple Silicon)
- **RAM**: Minimo 4GB, consigliati 8GB
- **Storage**: ~500MB per l'applicazione

### Software

| Componente | Versione Minima | Note |
|------------|-----------------|------|
| Node.js | 18+ | Per il frontend React |
| pnpm | 8+ | Package manager |
| Rust | 1.70+ | Per il backend Tauri |
| Python | 3.11+ | Per l'agent AI |
| uv | 0.4+ | Python package manager |

## Installazione per Sistema Operativo

=== "macOS"

    ### 1. Installa Homebrew (se non presente)

    ```bash
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    ```

    ### 2. Installa le dipendenze

    ```bash
    # Node.js e pnpm
    brew install node
    npm install -g pnpm

    # Rust
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
    source ~/.cargo/env

    # Python e uv
    brew install python@3.12
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

    ### 3. Installa dipendenze Tauri

    ```bash
    xcode-select --install
    ```

=== "Windows"

    ### 1. Installa i prerequisiti

    1. **Node.js**: Scarica da [nodejs.org](https://nodejs.org/) (LTS)
    2. **pnpm**: `npm install -g pnpm`
    3. **Rust**: Scarica da [rustup.rs](https://rustup.rs/)
    4. **Python 3.12**: Scarica da [python.org](https://www.python.org/downloads/)
    5. **uv**: `pip install uv`

    ### 2. Installa Visual Studio Build Tools

    Scarica e installa [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) con:
    - "Desktop development with C++"
    - Windows 10/11 SDK

    ### 3. Installa WebView2

    Scarica da [Microsoft Edge WebView2](https://developer.microsoft.com/en-us/microsoft-edge/webview2/)

=== "Linux (Ubuntu/Debian)"

    ### 1. Installa le dipendenze di sistema

    ```bash
    sudo apt update
    sudo apt install -y \
        build-essential \
        curl \
        wget \
        libssl-dev \
        libgtk-3-dev \
        libwebkit2gtk-4.1-dev \
        libappindicator3-dev \
        librsvg2-dev
    ```

    ### 2. Installa Node.js e pnpm

    ```bash
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt install -y nodejs
    npm install -g pnpm
    ```

    ### 3. Installa Rust

    ```bash
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
    source ~/.cargo/env
    ```

    ### 4. Installa Python e uv

    ```bash
    sudo apt install -y python3.12 python3.12-venv
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

=== "Linux (Fedora)"

    ### 1. Installa le dipendenze di sistema

    ```bash
    sudo dnf install -y \
        gcc \
        gcc-c++ \
        openssl-devel \
        gtk3-devel \
        webkit2gtk4.1-devel \
        libappindicator-gtk3-devel \
        librsvg2-devel
    ```

    ### 2. Installa Node.js e pnpm

    ```bash
    sudo dnf install -y nodejs
    npm install -g pnpm
    ```

    ### 3. Installa Rust

    ```bash
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
    source ~/.cargo/env
    ```

    ### 4. Installa Python e uv

    ```bash
    sudo dnf install -y python3.12
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

## Clona il Repository

```bash
git clone https://github.com/kanban-ai/kanban.git
cd kanban
```

## Setup del Progetto

### 1. Frontend (React + Tauri)

```bash
cd apps/desktop
pnpm install
```

### 2. Backend (Python Agent)

```bash
cd services/agent
uv sync
```

### 3. Configura le API Keys

Crea un file `.env` in `services/agent/`:

```bash
cd services/agent
cp .env.example .env
```

Modifica `.env` con le tue chiavi:

```env
# Scegli uno dei due provider
LLM_PROVIDER=anthropic  # oppure "openai"

# API Keys (almeno una richiesta)
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# Opzionale
DEBUG=false
HOST=127.0.0.1
PORT=8765
```

## Verifica l'Installazione

### Test Frontend

```bash
cd apps/desktop
pnpm dev
```

Dovresti vedere Vite avviarsi su `http://localhost:5173`.

### Test Agent

```bash
cd services/agent
uv run fastapi dev
```

Dovresti vedere FastAPI avviarsi su `http://localhost:8765`.

### Test Completo (Tauri)

```bash
cd apps/desktop
pnpm tauri dev
```

L'app desktop dovrebbe aprirsi.

## Troubleshooting

### Errore: "rust-analyzer not found"

```bash
rustup component add rust-analyzer
```

### Errore: "webkit2gtk not found" (Linux)

```bash
# Ubuntu/Debian
sudo apt install libwebkit2gtk-4.1-dev

# Fedora
sudo dnf install webkit2gtk4.1-devel
```

### Errore: "ANTHROPIC_API_KEY required"

Assicurati che il file `.env` sia in `services/agent/` e contenga una chiave valida.

### Errore: Python version mismatch

```bash
# Verifica versione Python
python3 --version  # Deve essere >= 3.11

# Se hai piu versioni, specifica quella corretta
uv python install 3.12
uv sync --python 3.12
```

## Prossimi Passi

- [Quick Start](quick-start.md) - Impara ad usare l'app
- [Configuration](configuration.md) - Personalizza le impostazioni
