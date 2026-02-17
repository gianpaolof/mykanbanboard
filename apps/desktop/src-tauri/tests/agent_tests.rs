//! Integration tests for the HTTP agent client layer.
//!
//! Because the agent functions use a hardcoded base URL (`http://localhost:8765/api`),
//! these tests exercise the same HTTP client construction and request/response patterns
//! using a configurable URL pointed at an httpmock server.  The helper functions
//! `kanban_ai::agent::build_agent_client` and `kanban_ai::agent::agent_base_url` are
//! the entry points used here.

use httpmock::prelude::*;
use serde_json::{json, Value};

// ---------------------------------------------------------------------------
// Test 1 – Timeout invariant (no mock needed)
// ---------------------------------------------------------------------------

/// Asserts that REQUEST_TIMEOUT_SECS > ANALYZE_TIMEOUT_SECS.
/// The Python agent has a hard 60-second analyse timeout; the Rust client
/// must wait at least that long before giving up, plus a safety buffer.
#[test]
fn test_request_timeout_greater_than_analyze_timeout() {
    let request_timeout = kanban_ai::agent::REQUEST_TIMEOUT_SECS;
    let analyze_timeout = kanban_ai::agent::ANALYZE_TIMEOUT_SECS;

    assert!(
        request_timeout > analyze_timeout,
        "REQUEST_TIMEOUT_SECS ({}) must be greater than ANALYZE_TIMEOUT_SECS ({}) \
         to ensure the client does not time out before the agent finishes analysing.",
        request_timeout,
        analyze_timeout
    );
}

// ---------------------------------------------------------------------------
// Test 2 – Triage success
// ---------------------------------------------------------------------------

#[tokio::test]
async fn test_triage_success() {
    let server = MockServer::start();

    let mock = server.mock(|when, then| {
        when.method(POST).path("/api/triage");
        then.status(200).json_body(json!({
            "priority": "high",
            "labels": ["bug", "backend"],
            "effort": "m",
            "reasoning": "The ticket describes a critical data loss issue."
        }));
    });

    let client = kanban_ai::agent::build_agent_client()
        .expect("Failed to build agent HTTP client");

    let url = format!("{}/api/triage", server.base_url());
    let body = json!({
        "ticketId": "T-001",
        "title": "Data loss on save",
        "description": "Saving a ticket sometimes silently drops the description field."
    });

    let response = client
        .post(&url)
        .json(&body)
        .send()
        .await
        .expect("HTTP request should succeed");

    assert_eq!(response.status(), 200, "Expected 200 OK from triage endpoint");

    let result: Value = response.json().await.expect("Response body should be valid JSON");
    assert_eq!(result["priority"], "high");
    assert_eq!(result["effort"], "m");
    assert!(result["labels"].as_array().unwrap().contains(&json!("bug")));

    mock.assert();
}

// ---------------------------------------------------------------------------
// Test 3 – Triage server error
// ---------------------------------------------------------------------------

#[tokio::test]
async fn test_triage_server_error() {
    let server = MockServer::start();

    let mock = server.mock(|when, then| {
        when.method(POST).path("/api/triage");
        then.status(500).body("Internal Server Error");
    });

    let client = kanban_ai::agent::build_agent_client()
        .expect("Failed to build agent HTTP client");

    let url = format!("{}/api/triage", server.base_url());
    let body = json!({
        "ticketId": "T-002",
        "title": "Test error handling",
        "description": "Should propagate 500 errors."
    });

    let response = client
        .post(&url)
        .json(&body)
        .send()
        .await
        .expect("HTTP transport should succeed even for 5xx responses");

    assert_eq!(response.status(), 500, "Expected 500 from the mock server");
    assert!(
        !response.status().is_success(),
        "A 500 response must not be considered successful"
    );

    mock.assert();
}

// ---------------------------------------------------------------------------
// Test 4 – Decompose success
// ---------------------------------------------------------------------------

#[tokio::test]
async fn test_decompose_success() {
    let server = MockServer::start();

    let mock = server.mock(|when, then| {
        when.method(POST).path("/api/decompose");
        then.status(200).json_body(json!({
            "subtasks": [
                {"title": "Design database schema", "description": "ERD for new feature"},
                {"title": "Implement API endpoint", "description": "POST /api/v2/items"},
                {"title": "Write unit tests", "description": "Cover happy and error paths"}
            ],
            "reasoning": "Decomposed into 3 logical subtasks."
        }));
    });

    let client = kanban_ai::agent::build_agent_client()
        .expect("Failed to build agent HTTP client");

    let url = format!("{}/api/decompose", server.base_url());
    let body = json!({
        "ticketId": "T-003",
        "title": "Add new items API",
        "description": "Implement the full items CRUD API with tests."
    });

    let response = client
        .post(&url)
        .json(&body)
        .send()
        .await
        .expect("HTTP request should succeed");

    assert_eq!(response.status(), 200);

    let result: Value = response.json().await.expect("Response should be valid JSON");
    let subtasks = result["subtasks"].as_array().expect("subtasks must be an array");
    assert_eq!(subtasks.len(), 3, "Expected 3 subtasks");

    mock.assert();
}

// ---------------------------------------------------------------------------
// Test 5 – Decompose invalid (malformed) JSON response
// ---------------------------------------------------------------------------

#[tokio::test]
async fn test_decompose_invalid_response() {
    let server = MockServer::start();

    let mock = server.mock(|when, then| {
        when.method(POST).path("/api/decompose");
        then.status(200)
            .header("content-type", "application/json")
            .body("{ this is not valid json !!!");
    });

    let client = kanban_ai::agent::build_agent_client()
        .expect("Failed to build agent HTTP client");

    let url = format!("{}/api/decompose", server.base_url());
    let body = json!({
        "ticketId": "T-004",
        "title": "Malformed response test",
        "description": ""
    });

    let response = client
        .post(&url)
        .json(&body)
        .send()
        .await
        .expect("HTTP transport should succeed");

    assert_eq!(response.status(), 200, "Mock returns 200 status");

    // Attempting to parse the malformed body as JSON must fail.
    let parse_result = response.json::<Value>().await;
    assert!(
        parse_result.is_err(),
        "Parsing malformed JSON body must return an error"
    );

    mock.assert();
}

// ---------------------------------------------------------------------------
// Test 6 – Chat success
// ---------------------------------------------------------------------------

#[tokio::test]
async fn test_chat_success() {
    let server = MockServer::start();

    let mock = server.mock(|when, then| {
        when.method(POST).path("/api/chat");
        then.status(200).json_body(json!({
            "response": "I found 3 tickets related to authentication.",
            "actions": [],
            "tickets_referenced": ["T-010", "T-011"]
        }));
    });

    let client = kanban_ai::agent::build_agent_client()
        .expect("Failed to build agent HTTP client");

    let url = format!("{}/api/chat", server.base_url());
    let body = json!({
        "message": "Which tickets are about authentication?",
        "context": null
    });

    let response = client
        .post(&url)
        .json(&body)
        .send()
        .await
        .expect("HTTP request should succeed");

    assert_eq!(response.status(), 200);

    let result: Value = response.json().await.expect("Response should be valid JSON");
    assert!(
        result["response"].as_str().unwrap().contains("3 tickets"),
        "Response text must match mock payload"
    );

    mock.assert();
}

// ---------------------------------------------------------------------------
// Test 7 – Chat with 408/timeout-like server error
// ---------------------------------------------------------------------------

#[tokio::test]
async fn test_chat_timeout_returns_error() {
    let server = MockServer::start();

    // Simulate the server returning a 408 Request Timeout status.
    let mock = server.mock(|when, then| {
        when.method(POST).path("/api/chat");
        then.status(408).body("Request Timeout");
    });

    let client = kanban_ai::agent::build_agent_client()
        .expect("Failed to build agent HTTP client");

    let url = format!("{}/api/chat", server.base_url());
    let body = json!({ "message": "slow query", "context": null });

    let response = client
        .post(&url)
        .json(&body)
        .send()
        .await
        .expect("Transport should succeed");

    assert_eq!(response.status(), 408);
    assert!(
        !response.status().is_success(),
        "A 408 response is not successful"
    );

    mock.assert();
}

// ---------------------------------------------------------------------------
// Test 8 – Agent base URL has correct format
// ---------------------------------------------------------------------------

#[test]
fn test_agent_url_construction() {
    let base_url = kanban_ai::agent::agent_base_url();

    // Must be an HTTP URL pointing to localhost on port 8765.
    assert!(
        base_url.starts_with("http://"),
        "Agent base URL must use the http scheme, got: {}",
        base_url
    );
    assert!(
        base_url.contains("localhost") || base_url.contains("127.0.0.1"),
        "Agent base URL must target localhost, got: {}",
        base_url
    );
    assert!(
        base_url.contains("8765"),
        "Agent base URL must use port 8765, got: {}",
        base_url
    );
    assert!(
        base_url.ends_with("/api"),
        "Agent base URL must end with /api, got: {}",
        base_url
    );
}

// ---------------------------------------------------------------------------
// Test 9 – Requests carry application/json Content-Type
// ---------------------------------------------------------------------------

#[tokio::test]
async fn test_request_headers_include_json_content_type() {
    let server = MockServer::start();

    // The mock only matches when the request carries the correct content-type.
    let mock = server.mock(|when, then| {
        when.method(POST)
            .path("/api/triage")
            .header("content-type", "application/json");
        then.status(200).json_body(json!({
            "priority": "low",
            "labels": [],
            "effort": "xs",
            "reasoning": "trivial"
        }));
    });

    let client = kanban_ai::agent::build_agent_client()
        .expect("Failed to build agent HTTP client");

    let url = format!("{}/api/triage", server.base_url());
    let body = json!({
        "ticketId": "T-005",
        "title": "Header check",
        "description": "Verify content-type is set correctly."
    });

    // `.json()` on reqwest automatically sets `Content-Type: application/json`.
    let response = client
        .post(&url)
        .json(&body)
        .send()
        .await
        .expect("HTTP request should succeed");

    assert_eq!(
        response.status(),
        200,
        "Mock must match because reqwest sets the correct content-type header"
    );

    mock.assert();
}

// ---------------------------------------------------------------------------
// Test 10 – Connection refused returns a transport error
// ---------------------------------------------------------------------------

#[tokio::test]
async fn test_connection_refused_returns_error() {
    // Port 19999 is assumed to have no listener.  If something actually runs
    // there the test will fail — acceptable in a controlled CI environment.
    let url = "http://127.0.0.1:19999/api/triage";

    let client = kanban_ai::agent::build_agent_client()
        .expect("Failed to build agent HTTP client");

    let body = json!({
        "ticketId": "T-999",
        "title": "Connection refused test",
        "description": "No server is listening on this port."
    });

    let result = client.post(url).json(&body).send().await;

    assert!(
        result.is_err(),
        "Connecting to a port with no listener must return an error"
    );

    let err_msg = result.unwrap_err().to_string();
    // reqwest wraps connection errors; the string should mention a connection-
    // level problem (the exact wording varies by OS).
    assert!(
        err_msg.contains("connect") || err_msg.contains("Connection") || err_msg.contains("error"),
        "Error message should describe a connection problem, got: {}",
        err_msg
    );
}
