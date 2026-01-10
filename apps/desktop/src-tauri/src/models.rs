use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};

// ===========================================
// ENUMS
// ===========================================

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "lowercase")]
pub enum Priority {
    Low,
    Medium,
    High,
    Critical,
}

impl Priority {
    pub fn as_str(&self) -> &str {
        match self {
            Priority::Low => "low",
            Priority::Medium => "medium",
            Priority::High => "high",
            Priority::Critical => "critical",
        }
    }

    pub fn from_str(s: &str) -> Option<Self> {
        match s {
            "low" => Some(Priority::Low),
            "medium" => Some(Priority::Medium),
            "high" => Some(Priority::High),
            "critical" => Some(Priority::Critical),
            _ => None,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "lowercase")]
pub enum Effort {
    Xs,
    S,
    M,
    L,
    Xl,
}

impl Effort {
    pub fn as_str(&self) -> &str {
        match self {
            Effort::Xs => "xs",
            Effort::S => "s",
            Effort::M => "m",
            Effort::L => "l",
            Effort::Xl => "xl",
        }
    }

    pub fn from_str(s: &str) -> Option<Self> {
        match s {
            "xs" => Some(Effort::Xs),
            "s" => Some(Effort::S),
            "m" => Some(Effort::M),
            "l" => Some(Effort::L),
            "xl" => Some(Effort::Xl),
            _ => None,
        }
    }
}

// ===========================================
// CORE MODELS
// ===========================================

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Board {
    pub id: String,
    pub name: String,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Column {
    pub id: String,
    pub name: String,
    pub position: i32,
    pub color: Option<String>,
    pub wip_limit: Option<i32>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Ticket {
    pub id: String,
    pub title: String,
    pub description: Option<String>,
    pub column_id: String,
    pub position: i32,
    pub priority: Option<Priority>,
    pub effort: Option<Effort>,
    pub due_date: Option<DateTime<Utc>>,
    pub labels: Vec<Label>,
    pub comments: Vec<Comment>,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Label {
    pub id: String,
    pub name: String,
    pub color: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Comment {
    pub id: String,
    pub ticket_id: String,
    pub content: String,
    pub created_at: DateTime<Utc>,
}

// ===========================================
// DTOs (Data Transfer Objects)
// ===========================================

#[derive(Debug, Clone, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct CreateTicket {
    pub title: String,
    pub description: Option<String>,
    pub column_id: String,
    pub priority: Option<Priority>,
    pub effort: Option<Effort>,
    pub labels: Option<Vec<String>>,
    pub due_date: Option<String>, // ISO 8601 string
}

#[derive(Debug, Clone, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct UpdateTicket {
    pub title: Option<String>,
    pub description: Option<String>,
    pub column_id: Option<String>,
    pub position: Option<i32>,
    pub priority: Option<Priority>,
    pub effort: Option<Effort>,
    pub labels: Option<Vec<String>>,
    pub due_date: Option<String>, // ISO 8601 string or null
}

#[derive(Debug, Clone, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct CreateColumn {
    pub name: String,
    pub color: Option<String>,
    pub wip_limit: Option<i32>,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct UpdateColumn {
    pub name: Option<String>,
    pub position: Option<i32>,
    pub color: Option<String>,
    pub wip_limit: Option<i32>,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct CreateLabel {
    pub name: String,
    pub color: String,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct UpdateLabel {
    pub name: Option<String>,
    pub color: Option<String>,
}
