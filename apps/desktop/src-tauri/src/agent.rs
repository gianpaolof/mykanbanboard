use crate::error::AppError;
use serde::Serialize;
use serde_json::Value;
use std::process::{Child, Command, Stdio};
use std::sync::Mutex;
use std::time::Duration;
use tauri::{AppHandle, Manager};
use tokio::time::sleep;

// Agent server configuration
const AGENT_BASE_URL: &str = "http://localhost:8765/api";
const REQUEST_TIMEOUT_SECS: u64 = 15;

// Sidecar configuration
const AGENT_STARTUP_TIMEOUT_SECS: u64 = 30;
const HEALTH_CHECK_INTERVAL_MS: u64 = 500;

// ===========================================
// SIDECAR PROCESS MANAGEMENT
// ===========================================

/// State container for the Python agent process
pub struct AgentProcess {
    child: Mutex<Option<Child>>,
}

impl AgentProcess {
    /// Create a new AgentProcess container
    pub fn new() -> Self {
        Self {
            child: Mutex::new(None),
        }
    }

    /// Store the child process
    pub fn set_child(&self, child: Child) {
        let mut lock = self.child.lock().unwrap();
        *lock = Some(child);
    }

    /// Kill the agent process if running
    pub fn kill(&self) {
        let mut lock = self.child.lock().unwrap();
        if let Some(ref mut child) = *lock {
            match child.kill() {
                Ok(_) => println!("Agent process killed successfully"),
                Err(e) => eprintln!("Failed to kill agent process: {}", e),
            }
        }
    }

    /// Check if the agent process is still running
    pub fn is_running(&self) -> bool {
        let mut lock = self.child.lock().unwrap();
        if let Some(ref mut child) = *lock {
            match child.try_wait() {
                Ok(None) => true, // Still running
                Ok(Some(status)) => {
                    eprintln!("Agent process exited with status: {}", status);
                    false
                }
                Err(e) => {
                    eprintln!("Error checking agent process status: {}", e);
                    false
                }
            }
        } else {
            false
        }
    }
}

impl Drop for AgentProcess {
    fn drop(&mut self) {
        self.kill();
    }
}

/// Start the Python agent sidecar
pub fn start_agent(app: &AppHandle) -> Result<(), String> {
    println!("Starting Python agent sidecar...");

    // Determine agent path based on dev vs production
    let agent_path = if cfg!(dev) {
        // In dev mode, use CARGO_MANIFEST_DIR to find the project root
        // CARGO_MANIFEST_DIR points to apps/desktop/src-tauri during build
        let manifest_dir = std::path::PathBuf::from(env!("CARGO_MANIFEST_DIR"));

        // Navigate up from src-tauri to project root (kanban/)
        manifest_dir
            .parent() // apps/desktop
            .and_then(|p| p.parent()) // apps
            .and_then(|p| p.parent()) // kanban (project root)
            .map(|p| p.join("services/agent"))
            .ok_or_else(|| "Failed to resolve agent path from CARGO_MANIFEST_DIR".to_string())?
    } else {
        // In production, bundle the agent with the app
        app.path()
            .resource_dir()
            .map_err(|e| format!("Failed to get resource dir: {}", e))?
            .join("agent")
    };

    println!("Agent path: {:?}", agent_path);

    // Check if path exists
    if !agent_path.exists() {
        return Err(format!(
            "Agent directory not found at: {}",
            agent_path.display()
        ));
    }

    // Check if uv is available
    let uv_check = Command::new("uv").arg("--version").output();
    if uv_check.is_err() {
        return Err(
            "uv not found. Please install uv: https://github.com/astral-sh/uv".to_string(),
        );
    }

    // Start the agent process
    let child = Command::new("uv")
        .args([
            "run",
            "uvicorn",
            "src.main:app",
            "--port",
            "8765",
            "--host",
            "127.0.0.1",
        ])
        .current_dir(&agent_path)
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .map_err(|e| format!("Failed to spawn agent process: {}", e))?;

    println!("Agent process started with PID: {:?}", child.id());

    // Store the child process in app state
    let agent_process: tauri::State<AgentProcess> = app.state();
    agent_process.set_child(child);

    // Spawn health check task
    let app_handle = app.clone();
    tauri::async_runtime::spawn(async move {
        if let Err(e) = wait_for_agent_ready(&app_handle).await {
            eprintln!("Agent health check failed: {}", e);
        }
    });

    Ok(())
}

/// Wait for the agent to be ready by polling the health endpoint
async fn wait_for_agent_ready(app: &AppHandle) -> Result<(), String> {
    let client = reqwest::Client::new();
    let health_url = "http://127.0.0.1:8765/";
    let start = std::time::Instant::now();

    println!("Waiting for agent to be ready...");

    loop {
        // Check if we've exceeded timeout
        if start.elapsed().as_secs() > AGENT_STARTUP_TIMEOUT_SECS {
            return Err(format!(
                "Agent failed to start within {} seconds",
                AGENT_STARTUP_TIMEOUT_SECS
            ));
        }

        // Check if process is still running
        let agent_process: tauri::State<AgentProcess> = app.state();
        if !agent_process.is_running() {
            return Err("Agent process died unexpectedly".to_string());
        }

        // Try to connect to health endpoint
        match client
            .get(health_url)
            .timeout(Duration::from_secs(2))
            .send()
            .await
        {
            Ok(response) if response.status().is_success() => {
                println!("Agent is ready! (took {:?})", start.elapsed());
                return Ok(());
            }
            Ok(response) => {
                println!("Agent responded with status: {}", response.status());
            }
            Err(_) => {
                // Connection failed, wait and retry
            }
        }

        sleep(Duration::from_millis(HEALTH_CHECK_INTERVAL_MS)).await;
    }
}

/// Stop the Python agent sidecar
pub fn stop_agent(app: &AppHandle) {
    println!("Stopping Python agent sidecar...");
    let agent_process: tauri::State<AgentProcess> = app.state();
    agent_process.kill();
}

// ===========================================
// REQUEST/RESPONSE TYPES
// ===========================================

#[derive(Debug, Serialize)]
struct TriageRequest {
    ticket_id: String,
    title: String,
    description: String,
}

#[derive(Debug, Serialize)]
struct DecomposeRequest {
    ticket_id: String,
    title: String,
    description: String,
}

#[derive(Debug, Serialize)]
struct ChatRequest {
    message: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    context: Option<Value>,
}

#[derive(Debug, Serialize)]
struct SearchRequest {
    query: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    limit: Option<i32>,
}

#[derive(Debug, Clone, Serialize, serde::Deserialize)]
pub struct DailySummaryTicket {
    pub id: String,
    pub title: String,
    #[serde(default)]
    pub description: String,
    #[serde(default)]
    pub status: String,
    #[serde(default)]
    pub priority: String,
    #[serde(default)]
    pub labels: Vec<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub due_date: Option<String>,
    #[serde(default)]
    pub column_id: String,
}

#[derive(Debug, Serialize, serde::Deserialize)]
pub struct DailySummaryRequest {
    pub in_progress: Vec<DailySummaryTicket>,
    pub blocked: Vec<DailySummaryTicket>,
    pub due_soon: Vec<DailySummaryTicket>,
    pub recently_completed: Vec<DailySummaryTicket>,
}

#[derive(Debug, Serialize, serde::Deserialize)]
pub struct SyncTicketsRequest {
    pub tickets: Vec<DailySummaryTicket>,
    #[serde(default)]
    pub force_full_sync: bool,
}

// ===========================================
// AGENT COMMANDS
// ===========================================

/// Triage a ticket: auto-assign priority, labels, and effort estimate
#[tauri::command]
pub async fn agent_triage(
    ticket_id: String,
    title: String,
    description: String,
) -> Result<Value, String> {
    let client = create_http_client()?;
    let url = format!("{}/triage", AGENT_BASE_URL);

    let request_body = TriageRequest {
        ticket_id,
        title,
        description,
    };

    let response = client
        .post(&url)
        .json(&request_body)
        .send()
        .await
        .map_err(|e| AppError::Http(format!("Failed to connect to agent: {}", e)))?;

    if !response.status().is_success() {
        let status = response.status();
        let error_text = response
            .text()
            .await
            .unwrap_or_else(|_| "Unknown error".to_string());
        return Err(AppError::Agent(format!(
            "Agent returned error {}: {}",
            status, error_text
        ))
        .into());
    }

    let result: Value = response
        .json()
        .await
        .map_err(|e| AppError::Http(format!("Failed to parse agent response: {}", e)))?;

    Ok(result)
}

/// Decompose a complex task into subtasks
#[tauri::command]
pub async fn agent_decompose(
    ticket_id: String,
    title: String,
    description: String,
) -> Result<Value, String> {
    let client = create_http_client()?;
    let url = format!("{}/decompose", AGENT_BASE_URL);

    let request_body = DecomposeRequest {
        ticket_id,
        title,
        description,
    };

    let response = client
        .post(&url)
        .json(&request_body)
        .send()
        .await
        .map_err(|e| AppError::Http(format!("Failed to connect to agent: {}", e)))?;

    if !response.status().is_success() {
        let status = response.status();
        let error_text = response
            .text()
            .await
            .unwrap_or_else(|_| "Unknown error".to_string());
        return Err(AppError::Agent(format!(
            "Agent returned error {}: {}",
            status, error_text
        ))
        .into());
    }

    let result: Value = response
        .json()
        .await
        .map_err(|e| AppError::Http(format!("Failed to parse agent response: {}", e)))?;

    Ok(result)
}

/// Chat with the AI agent
#[tauri::command]
pub async fn agent_chat(message: String, context: Option<Value>) -> Result<Value, String> {
    let client = create_http_client()?;
    let url = format!("{}/chat", AGENT_BASE_URL);

    let request_body = ChatRequest { message, context };

    let response = client
        .post(&url)
        .json(&request_body)
        .send()
        .await
        .map_err(|e| AppError::Http(format!("Failed to connect to agent: {}", e)))?;

    if !response.status().is_success() {
        let status = response.status();
        let error_text = response
            .text()
            .await
            .unwrap_or_else(|_| "Unknown error".to_string());
        return Err(AppError::Agent(format!(
            "Agent returned error {}: {}",
            status, error_text
        ))
        .into());
    }

    let result: Value = response
        .json()
        .await
        .map_err(|e| AppError::Http(format!("Failed to parse agent response: {}", e)))?;

    Ok(result)
}

/// Generate daily summary of tickets
/// Now requires actual ticket data for meaningful summaries
#[tauri::command]
pub async fn agent_daily_summary(request: DailySummaryRequest) -> Result<Value, String> {
    let client = create_http_client()?;
    let url = format!("{}/daily-summary", AGENT_BASE_URL);

    let response = client
        .post(&url)
        .json(&request)
        .send()
        .await
        .map_err(|e| AppError::Http(format!("Failed to connect to agent: {}", e)))?;

    if !response.status().is_success() {
        let status = response.status();
        let error_text = response
            .text()
            .await
            .unwrap_or_else(|_| "Unknown error".to_string());
        return Err(AppError::Agent(format!(
            "Agent returned error {}: {}",
            status, error_text
        ))
        .into());
    }

    let result: Value = response
        .json()
        .await
        .map_err(|e| AppError::Http(format!("Failed to parse agent response: {}", e)))?;

    Ok(result)
}

/// Semantic search for tickets
#[tauri::command]
pub async fn agent_search(query: String, limit: Option<i32>) -> Result<Value, String> {
    let client = create_http_client()?;
    let url = format!("{}/search", AGENT_BASE_URL);

    let request_body = SearchRequest { query, limit };

    let response = client
        .post(&url)
        .json(&request_body)
        .send()
        .await
        .map_err(|e| AppError::Http(format!("Failed to connect to agent: {}", e)))?;

    if !response.status().is_success() {
        let status = response.status();
        let error_text = response
            .text()
            .await
            .unwrap_or_else(|_| "Unknown error".to_string());
        return Err(AppError::Agent(format!(
            "Agent returned error {}: {}",
            status, error_text
        ))
        .into());
    }

    let result: Value = response
        .json()
        .await
        .map_err(|e| AppError::Http(format!("Failed to parse agent response: {}", e)))?;

    Ok(result)
}

/// Check if agent is available and healthy
#[tauri::command]
pub async fn agent_health() -> Result<bool, String> {
    let client = create_http_client()?;
    let url = format!("{}/health", AGENT_BASE_URL);

    match client.get(&url).send().await {
        Ok(response) => Ok(response.status().is_success()),
        Err(_) => Ok(false), // Agent not available, return false instead of error
    }
}

/// Sync tickets to ChromaDB for semantic search
#[tauri::command]
pub async fn agent_sync_tickets(request: SyncTicketsRequest) -> Result<Value, String> {
    let client = create_http_client()?;
    let url = format!("{}/sync-tickets", AGENT_BASE_URL);

    let response = client
        .post(&url)
        .json(&request)
        .send()
        .await
        .map_err(|e| AppError::Http(format!("Failed to connect to agent: {}", e)))?;

    if !response.status().is_success() {
        let status = response.status();
        let error_text = response
            .text()
            .await
            .unwrap_or_else(|_| "Unknown error".to_string());
        return Err(AppError::Agent(format!(
            "Agent returned error {}: {}",
            status, error_text
        ))
        .into());
    }

    let result: Value = response
        .json()
        .await
        .map_err(|e| AppError::Http(format!("Failed to parse agent response: {}", e)))?;

    Ok(result)
}

/// Get ChromaDB sync status
#[tauri::command]
pub async fn agent_sync_status() -> Result<Value, String> {
    let client = create_http_client()?;
    let url = format!("{}/context/sync-status", AGENT_BASE_URL);

    let response = client
        .get(&url)
        .send()
        .await
        .map_err(|e| AppError::Http(format!("Failed to connect to agent: {}", e)))?;

    if !response.status().is_success() {
        let status = response.status();
        let error_text = response
            .text()
            .await
            .unwrap_or_else(|_| "Unknown error".to_string());
        return Err(AppError::Agent(format!(
            "Agent returned error {}: {}",
            status, error_text
        ))
        .into());
    }

    let result: Value = response
        .json()
        .await
        .map_err(|e| AppError::Http(format!("Failed to parse agent response: {}", e)))?;

    Ok(result)
}

/// Invalidate context cache
#[tauri::command]
pub async fn agent_invalidate_cache(board_id: Option<String>) -> Result<Value, String> {
    let client = create_http_client()?;
    let mut url = format!("{}/context/invalidate-cache", AGENT_BASE_URL);

    if let Some(ref id) = board_id {
        url = format!("{}?board_id={}", url, id);
    }

    let response = client
        .post(&url)
        .send()
        .await
        .map_err(|e| AppError::Http(format!("Failed to connect to agent: {}", e)))?;

    if !response.status().is_success() {
        let status = response.status();
        let error_text = response
            .text()
            .await
            .unwrap_or_else(|_| "Unknown error".to_string());
        return Err(AppError::Agent(format!(
            "Agent returned error {}: {}",
            status, error_text
        ))
        .into());
    }

    let result: Value = response
        .json()
        .await
        .map_err(|e| AppError::Http(format!("Failed to parse agent response: {}", e)))?;

    Ok(result)
}

/// Get cache statistics
#[tauri::command]
pub async fn agent_cache_stats() -> Result<Value, String> {
    let client = create_http_client()?;
    let url = format!("{}/context/cache-stats", AGENT_BASE_URL);

    let response = client
        .get(&url)
        .send()
        .await
        .map_err(|e| AppError::Http(format!("Failed to connect to agent: {}", e)))?;

    if !response.status().is_success() {
        let status = response.status();
        let error_text = response
            .text()
            .await
            .unwrap_or_else(|_| "Unknown error".to_string());
        return Err(AppError::Agent(format!(
            "Agent returned error {}: {}",
            status, error_text
        ))
        .into());
    }

    let result: Value = response
        .json()
        .await
        .map_err(|e| AppError::Http(format!("Failed to parse agent response: {}", e)))?;

    Ok(result)
}

// ===========================================
// HELPER FUNCTIONS
// ===========================================

/// Create HTTP client with timeout
fn create_http_client() -> Result<reqwest::Client, String> {
    reqwest::Client::builder()
        .timeout(std::time::Duration::from_secs(REQUEST_TIMEOUT_SECS))
        .build()
        .map_err(|e| AppError::Http(format!("Failed to create HTTP client: {}", e)).into())
}
