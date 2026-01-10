# Python Sidecar Implementation for Tauri

## Overview

This document describes the implementation of the Python agent sidecar management system for Kanban AI's Tauri desktop application.

## Architecture

The sidecar management system automatically starts and stops the Python FastAPI agent server when the Tauri app launches and closes.

```
┌─────────────────────────────────────────┐
│         Tauri Desktop App               │
│  ┌───────────────────────────────────┐  │
│  │   lib.rs (App Entry Point)        │  │
│  │   - Initialize AgentProcess       │  │
│  │   - Start agent on setup          │  │
│  │   - Stop agent on window destroy  │  │
│  └────────────┬──────────────────────┘  │
│               │                          │
│  ┌────────────▼──────────────────────┐  │
│  │   agent.rs (Process Manager)      │  │
│  │   - AgentProcess state            │  │
│  │   - start_agent()                 │  │
│  │   - stop_agent()                  │  │
│  │   - wait_for_agent_ready()        │  │
│  └────────────┬──────────────────────┘  │
└───────────────┼──────────────────────────┘
                │ spawns & manages
                ▼
┌───────────────────────────────────────────┐
│    Python Agent Sidecar Process           │
│    uv run uvicorn src.main:app            │
│    Port: 8765                             │
└───────────────────────────────────────────┘
```

## Components

### 1. AgentProcess State (`agent.rs`)

A thread-safe state container that holds the Python process handle:

```rust
pub struct AgentProcess {
    child: Mutex<Option<Child>>,
}
```

**Methods:**
- `new()` - Create empty state container
- `set_child(child)` - Store the spawned process
- `kill()` - Terminate the process
- `is_running()` - Check if process is alive

**Lifecycle:**
- Automatically kills the process on Drop (when app closes)

### 2. start_agent() Function

Starts the Python agent sidecar with proper path resolution:

**Dev Mode:**
- Resolves path to `../../services/agent` from Tauri binary
- Uses `uv run uvicorn src.main:app --port 8765 --host 127.0.0.1`

**Production Mode:**
- Looks for bundled agent in `{resource_dir}/agent`
- Same startup command

**Features:**
- Validates `uv` is installed
- Validates agent directory exists
- Captures stdout/stderr for logging
- Spawns async health check task
- Stores process in app state

### 3. wait_for_agent_ready() Function

Asynchronous health check loop that waits for the agent to be ready:

**Behavior:**
- Polls `http://127.0.0.1:8765/` every 500ms
- Times out after 30 seconds
- Checks if process is still alive
- Returns success when HTTP 200 received

**Timeout Configuration:**
```rust
const AGENT_STARTUP_TIMEOUT_SECS: u64 = 30;
const HEALTH_CHECK_INTERVAL_MS: u64 = 500;
```

### 4. stop_agent() Function

Gracefully terminates the agent process:

```rust
pub fn stop_agent(app: &AppHandle) {
    let agent_process: tauri::State<AgentProcess> = app.state();
    agent_process.kill();
}
```

### 5. Integration in lib.rs

**Setup Hook:**
```rust
.setup(|app| {
    // ... database setup ...

    // Initialize agent process state
    app.manage(AgentProcess::new());

    // Start Python agent sidecar
    if let Err(e) = start_agent(app.handle()) {
        eprintln!("Failed to start agent: {}", e);
        eprintln!("Agent features will be unavailable");
    }

    Ok(())
})
```

**Cleanup Hook:**
```rust
.on_window_event(|window, event| {
    if let tauri::WindowEvent::Destroyed = event {
        stop_agent(window.app_handle());
    }
})
```

## Error Handling

The implementation gracefully handles errors:

1. **UV Not Installed**
   - Returns error: "uv not found. Please install uv: https://github.com/astral-sh/uv"
   - Agent features remain unavailable but app continues

2. **Agent Directory Not Found**
   - Returns error with path
   - Agent features remain unavailable but app continues

3. **Process Spawn Failure**
   - Logs error message
   - Agent features remain unavailable but app continues

4. **Startup Timeout**
   - Health check fails after 30 seconds
   - Process is killed
   - Agent features remain unavailable

5. **Process Crash**
   - Detected during health check
   - Error logged with exit status
   - Agent features remain unavailable

## Configuration

### Python Agent Requirements

The agent must:
- Be located at `services/agent/` (dev) or `{resource_dir}/agent` (production)
- Have a `src/main.py` with FastAPI app named `app`
- Listen on port 8765, host 127.0.0.1
- Respond to `GET /` with HTTP 200 when ready

### Environment Variables

The agent requires environment variables (via `.env` file):
- `ANTHROPIC_API_KEY` - Required for Claude API
- `OPENAI_API_KEY` - Optional fallback
- Other config in `services/agent/.env.example`

## Usage

### Development

1. Install `uv` if not present:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Create `.env` file in `services/agent/`:
```bash
cd services/agent
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

3. Run Tauri dev:
```bash
cd apps/desktop
pnpm tauri dev
```

The agent will start automatically and be available at `http://127.0.0.1:8765`.

### Production

For production builds, bundle the Python agent:

1. Copy `services/agent/` to `{resource_dir}/agent` during build
2. Include `uv` binary or use system installation
3. Include `.env` file or use environment variables

## Monitoring

### Logs

The sidecar manager logs to stdout/stderr:

```
Starting Python agent sidecar...
Agent path: "/Users/user/kanban/services/agent"
Agent process started with PID: 12345
Waiting for agent to be ready...
Agent is ready! (took 2.3s)
```

### Health Check

Use the `agent_health` Tauri command:

```rust
#[tauri::command]
pub async fn agent_health() -> Result<bool, String>
```

From frontend:
```typescript
const isHealthy = await invoke('agent_health');
```

## Testing

### Manual Testing

1. Start the app in dev mode
2. Check console logs for "Agent is ready!"
3. Test agent endpoint:
```bash
curl http://127.0.0.1:8765/
```

4. Close the app
5. Verify agent process is terminated:
```bash
lsof -i :8765  # Should show nothing
```

### Error Scenarios

**Test without `uv`:**
```bash
# Temporarily rename uv
which uv  # Note the path
sudo mv $(which uv) $(which uv).bak
# Run app - should see "uv not found" error
sudo mv $(which uv).bak $(which uv)
```

**Test without .env:**
```bash
cd services/agent
mv .env .env.bak
# Run app - agent will fail to start (missing API key)
mv .env.bak .env
```

## Future Improvements

1. **Agent Auto-Restart**
   - Monitor process health during runtime
   - Restart if crashed

2. **Better Logging**
   - Stream agent stdout/stderr to Tauri logs
   - Structured logging with timestamps

3. **Graceful Shutdown**
   - Send SIGTERM before SIGKILL
   - Wait for graceful shutdown timeout

4. **Production Bundling**
   - Bundle Python runtime with app
   - Use pyinstaller or similar
   - Self-contained executable

5. **Port Management**
   - Auto-select available port if 8765 is taken
   - Pass port to agent via env var

## Dependencies

**Rust Crates:**
- `tauri` - App framework
- `tokio` - Async runtime
- `reqwest` - HTTP client for health checks
- `serde` - Serialization

**Python Requirements:**
- `uv` - Package manager and runner
- `uvicorn` - ASGI server
- `fastapi` - Web framework
- Dependencies in `services/agent/pyproject.toml`

## Troubleshooting

### Agent Won't Start

1. Check `uv` is installed: `uv --version`
2. Check agent path exists: `ls services/agent/src/main.py`
3. Check `.env` file exists: `ls services/agent/.env`
4. Check API key is valid in `.env`
5. Try starting agent manually:
   ```bash
   cd services/agent
   uv run uvicorn src.main:app --port 8765
   ```

### Port Already in Use

If port 8765 is already taken:
```bash
# Find process using port
lsof -i :8765

# Kill it
kill -9 <PID>
```

### Health Check Timeout

If agent starts but health check times out:
1. Increase `AGENT_STARTUP_TIMEOUT_SECS`
2. Check agent logs for startup errors
3. Verify agent responds to `GET /`
4. Check firewall/network settings

## Implementation Checklist

- [x] Create AgentProcess state struct
- [x] Implement start_agent() function
- [x] Implement stop_agent() function
- [x] Implement wait_for_agent_ready() health check
- [x] Integrate into lib.rs setup hook
- [x] Integrate into window event handler
- [x] Add reqwest dependency
- [x] Handle dev vs production paths
- [x] Validate uv installation
- [x] Validate agent directory
- [x] Capture process stdout/stderr
- [x] Implement Drop cleanup
- [x] Test compilation
- [ ] Test runtime behavior
- [ ] Document usage
- [ ] Add production bundling config
