# Enterprise Onboarding Copilot - System Design Document

## 1. Overview

The Enterprise Onboarding Copilot is a production-style, multi-agent, RAG-powered onboarding assistant designed to help new employees navigate their first days at a company. It combines modern AI/ML techniques with solid software engineering practices, including comprehensive authentication, authorization, and audit logging.

### 1.1 Key Capabilities

- **Multi-Agent Architecture**: Specialized agents for HR, IT, Security, Finance, and Progress tracking
- **Hybrid RAG**: Semantic search + BM25 keyword search with Reciprocal Rank Fusion
- **ML-Powered Routing**: Classical ML classifier for query department routing
- **Production Security**: JWT auth, RBAC, session management, PII detection, audit logging
- **MLOps**: Experiment tracking, model versioning, and metrics via MLflow

## 2. Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                   Clients                                    │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │   Web Browser   │  │   Mobile App    │  │   API Client    │             │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘             │
└───────────┼─────────────────────┼─────────────────────┼─────────────────────┘
            │                     │                     │
            └─────────────────────┼─────────────────────┘
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            API Gateway / Load Balancer                       │
│                              (Rate Limiting, Auth)                           │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FastAPI Backend                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     Security & Middleware Layer                       │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐             │   │
│  │  │   JWT    │  │   RBAC   │  │   Rate   │  │  Audit   │             │   │
│  │  │   Auth   │  │  Check   │  │  Limit   │  │  Logger  │             │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘             │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐                           │   │
│  │  │   PII    │  │ Session  │  │ Metrics  │                           │   │
│  │  │ Redactor │  │  Cache   │  │Collector │                           │   │
│  │  └──────────┘  └──────────┘  └──────────┘                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                     │                                        │
│                                     ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      Multi-Agent Orchestrator                         │   │
│  │                          (LangGraph)                                  │   │
│  │  ┌─────────────┐                                                     │   │
│  │  │ Coordinator │──┐                                                  │   │
│  │  └─────────────┘  │   ┌──────────────────────────────────────┐      │   │
│  │                    │   │        Specialist Agents              │      │   │
│  │  ┌─────────────┐  │   │  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐    │      │   │
│  │  │  ML Router  │──┼──▶│  │ HR  │ │ IT  │ │ Sec │ │ Fin │    │      │   │
│  │  │  (TF-IDF +  │  │   │  └─────┘ └─────┘ └─────┘ └─────┘    │      │   │
│  │  │  LogReg)    │  │   │          ┌──────────────┐            │      │   │
│  │  └─────────────┘  │   │          │   Progress   │            │      │   │
│  │                    │   │          └──────────────┘            │      │   │
│  │                    │   └──────────────────────────────────────┘      │   │
│  └────────────────────┼─────────────────────────────────────────────────┘   │
│                       │                                                      │
│                       ▼                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      Hybrid RAG Pipeline                              │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────┐  │   │
│  │  │  Embedding  │  │  Semantic   │  │    BM25     │  │    RRF    │  │   │
│  │  │  Service    │  │   Search    │  │   Search    │  │  Rerank   │  │   │
│  │  │(HuggingFace)│  │ (ChromaDB)  │  │ (rank_bm25) │  │  Fusion   │  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └───────────┘  │   │
│  │                                                            │        │   │
│  │                                                            ▼        │   │
│  │                                              ┌─────────────────────┐│   │
│  │                                              │  Answer Generation  ││   │
│  │                                              │     (OpenAI LLM)    ││   │
│  │                                              └─────────────────────┘│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────┬─────────────────────────────────────┘
                                        │
            ┌───────────────────────────┼───────────────────────────┐
            ▼                           ▼                           ▼
┌───────────────────┐      ┌───────────────────┐      ┌───────────────────┐
│      SQLite       │      │     ChromaDB      │      │      MLflow       │
│  - Users          │      │  - Embeddings     │      │  - Experiments    │
│  - Tasks          │      │  - Metadata       │      │  - Models         │
│  - Messages       │      │  - Document IDs   │      │  - Metrics        │
│  - Sessions       │      │                   │      │  - Artifacts      │
│  - Audit Logs     │      │                   │      │                   │
│  - Routing Logs   │      │                   │      │                   │
│  - System Metrics │      │                   │      │                   │
└───────────────────┘      └───────────────────┘      └───────────────────┘
```

### 2.2 Component Details

#### 2.2.1 API Layer (FastAPI)

The API layer handles all HTTP requests and provides:
- RESTful endpoints for chat, tasks, users, auth, and admin operations
- Request validation using Pydantic v2 models
- CORS configuration for frontend communication
- JWT-based authentication with refresh tokens
- Role-based access control (RBAC) with granular permissions
- Rate limiting middleware (token bucket algorithm)
- PII detection and redaction before logging
- Comprehensive audit logging for compliance
- Prometheus metrics endpoint

**Key Endpoints:**

| Category | Endpoint | Method | Description |
|----------|----------|--------|-------------|
| Auth | `/api/v1/auth/login` | POST | User authentication |
| Auth | `/api/v1/auth/register` | POST | User registration |
| Auth | `/api/v1/auth/refresh` | POST | Token refresh |
| Auth | `/api/v1/auth/logout` | POST | Session invalidation |
| Chat | `/api/v1/chat` | POST | Main chat interface |
| Tasks | `/api/v1/tasks` | GET | Task list |
| Tasks | `/api/v1/tasks/{id}/status` | POST | Update task status |
| Admin | `/api/v1/admin/metrics` | GET | Dashboard metrics |
| Admin | `/api/v1/admin/users` | GET | All users progress |
| Monitoring | `/api/v1/health` | GET | Health check |
| Monitoring | `/api/v1/metrics` | GET | Prometheus metrics |

#### 2.2.2 Multi-Agent System (LangGraph)

The agent system uses LangGraph for orchestration with a state machine approach:

```
                    ┌──────────────────┐
                    │   User Message   │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │   Coordinator    │
                    │     Agent        │
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
        ┌─────────┐   ┌─────────┐   ┌─────────┐
        │ML Router│   │ Keyword │   │ Context │
        │Predict  │   │ Rules   │   │  Rules  │
        └────┬────┘   └────┬────┘   └────┬────┘
              │              │              │
              └──────────────┼──────────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ Final Department │
                    │    Selection     │
                    └────────┬─────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │         │         │         │         │
         ▼         ▼         ▼         ▼         ▼
    ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
    │   HR   │ │   IT   │ │Security│ │Finance │ │Progress│
    │ Agent  │ │ Agent  │ │ Agent  │ │ Agent  │ │ Agent  │
    └────┬───┘ └────┬───┘ └────┬───┘ └────┬───┘ └────┬───┘
         │         │         │         │         │
         └─────────┼─────────┼─────────┼─────────┘
                   │         │         │
                   ▼         ▼         ▼
              ┌─────────────────────────────┐
              │     Hybrid RAG Retrieval    │
              └─────────────────────────────┘
                             │
                             ▼
              ┌─────────────────────────────┐
              │      Response Generation    │
              │         (OpenAI LLM)        │
              └─────────────────────────────┘
```

**Agent State Schema:**

```python
class AgentState(TypedDict):
    # User context
    user_id: int
    user_name: str
    user_role: str          # Job role (e.g., "Engineer")
    user_department: str    # Work department
    user_type: str          # Access level (new_hire, admin)
    
    # Conversation
    messages: List[Dict]    # Chat history
    current_message: str    # Current user message
    
    # Routing
    predicted_department: str
    prediction_confidence: float
    final_department: str
    was_overridden: bool
    
    # Response
    response: str
    sources: List[Dict]
    task_updates: List[Dict]
    
    # Tasks
    tasks: List[Dict]
```

**Agent Responsibilities:**

| Agent | Responsibility | Data Sources |
|-------|---------------|--------------|
| Coordinator | Route queries, apply rules | ML Model, Keywords |
| HR Agent | Benefits, PTO, policies | hr_policies.md |
| IT Agent | Devices, accounts, tools | it_policies.md |
| Security Agent | Training, compliance | security_policies.md |
| Finance Agent | Payroll, expenses | finance_policies.md |
| Progress Agent | Task tracking | Database |

#### 2.2.3 Hybrid RAG Pipeline

The RAG system uses a hybrid approach combining semantic and keyword search:

```
┌──────────────────────────────────────────────────────────────────┐
│                    Document Ingestion Pipeline                    │
│                                                                   │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐          │
│  │  Load   │ → │  Parse  │ → │  Chunk  │ → │  Embed  │          │
│  │  Docs   │   │Markdown │   │ (500c)  │   │ (768d)  │          │
│  └─────────┘   └─────────┘   └─────────┘   └─────────┘          │
│       │                                          │                │
│       ▼                                          ▼                │
│  ┌─────────────────┐                    ┌──────────────┐         │
│  │ BM25 Corpus     │                    │   ChromaDB   │         │
│  │ (in-memory)     │                    │ (persistent) │         │
│  └─────────────────┘                    └──────────────┘         │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                    Hybrid Query Pipeline                          │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                         Query                                │ │
│  └────────────────────────────┬────────────────────────────────┘ │
│                               │                                   │
│               ┌───────────────┴───────────────┐                  │
│               ▼                               ▼                   │
│  ┌────────────────────────┐      ┌────────────────────────┐     │
│  │    Semantic Search     │      │     BM25 Search        │     │
│  │    (ChromaDB)          │      │     (rank_bm25)        │     │
│  │                        │      │                        │     │
│  │  • Embed query         │      │  • Tokenize query      │     │
│  │  • Cosine similarity   │      │  • TF-IDF scoring      │     │
│  │  • Top-K results       │      │  • Top-K results       │     │
│  └───────────┬────────────┘      └───────────┬────────────┘     │
│               │                               │                   │
│               └───────────────┬───────────────┘                  │
│                               ▼                                   │
│              ┌────────────────────────────────┐                  │
│              │   Reciprocal Rank Fusion (RRF) │                  │
│              │                                │                  │
│              │   score = Σ 1/(k + rank_i)     │                  │
│              │   k = 60 (smoothing factor)    │                  │
│              └───────────────┬────────────────┘                  │
│                               │                                   │
│                               ▼                                   │
│              ┌────────────────────────────────┐                  │
│              │      Confidence Scoring        │                  │
│              │  • Distance-based confidence   │                  │
│              │  • Result count adjustment     │                  │
│              └───────────────┬────────────────┘                  │
│                               │                                   │
│                               ▼                                   │
│              ┌────────────────────────────────┐                  │
│              │       Answer Generation        │                  │
│              │        (GPT-4o-mini)           │                  │
│              │                                │                  │
│              │  • Grounded in context         │                  │
│              │  • Markdown formatting         │                  │
│              │  • Source attribution          │                  │
│              └────────────────────────────────┘                  │
└──────────────────────────────────────────────────────────────────┘
```

**Configuration:**
- Embedding Model: `sentence-transformers/all-mpnet-base-v2` (768 dimensions)
- Chunk Size: 500 characters
- Chunk Overlap: 50 characters
- Top-K Retrieval: 5 documents
- Vector Store: ChromaDB with cosine similarity
- BM25: Okapi BM25 with k1=1.5, b=0.75
- RRF k-factor: 60

**Confidence Scoring:**
```python
# Confidence based on semantic distances
confidence = 1 - (avg_distance / 2)  # Normalize to 0-1

# Adjust for result count
if len(results) < top_k:
    confidence *= (len(results) / top_k) * 0.8

# Classification
if confidence > 0.7: level = "HIGH"
elif confidence > 0.4: level = "MEDIUM"
else: level = "LOW"
```

#### 2.2.4 ML Routing Model

The routing model is a classical ML classifier:

```
┌──────────────────────────────────────────────────────────────┐
│                    Training Pipeline                          │
│                                                               │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐      │
│  │ Labeled │ → │ TF-IDF  │ → │ Logistic│ → │ MLflow  │      │
│  │  Data   │   │Vectorize│   │Regression│   │ Log    │      │
│  │ (JSON)  │   │(5000 f) │   │(balanced)│   │        │      │
│  └─────────┘   └─────────┘   └─────────┘   └─────────┘      │
│                                               │               │
│                                               ▼               │
│                                     ┌──────────────────┐     │
│                                     │ Model Artifacts  │     │
│                                     │ • .joblib model  │     │
│                                     │ • labels.json    │     │
│                                     └──────────────────┘     │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                    Inference Pipeline                         │
│                                                               │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐      │
│  │  Query  │ → │ TF-IDF  │ → │ Predict │ → │ Keyword │      │
│  │  Text   │   │ Transform│  │+ Proba  │   │Override │      │
│  └─────────┘   └─────────┘   └─────────┘   └─────────┘      │
│                                               │               │
│                                               ▼               │
│                              ┌────────────────────────────┐  │
│                              │ Final Routing Decision     │  │
│                              │ • Department               │  │
│                              │ • Confidence score         │  │
│                              │ • Override flag            │  │
│                              └────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

**Model Details:**
- Input: TF-IDF features (max 5000, unigrams + bigrams)
- Output: 5 classes (HR, IT, Security, Finance, General)
- Algorithm: Logistic Regression with balanced class weights
- Evaluation: Accuracy, Precision, Recall, F1 (macro/weighted)
- Override Rules: Keyword matching with word boundaries

**Keyword Override Rules:**
```python
DEPARTMENT_KEYWORDS = {
    "HR": ["benefits", "insurance", "401k", "pto", "vacation", ...],
    "IT": ["laptop", "vpn", "password", "email", "software", ...],
    "Security": ["training", "compliance", "nda", "access", ...],
    "Finance": ["expense", "payroll", "reimbursement", ...],
}

# Override logic:
# 1. If keyword matches ML prediction → confirm
# 2. If ML confidence < threshold and keyword match → override
# 3. Otherwise → use ML prediction
```

### 2.3 Data Flow

#### 2.3.1 Chat Request Flow

```
1. User sends message via UI
   │
2. POST /api/v1/chat with JWT token
   │
3. AuditMiddleware: Log request start
   │
4. SecurityMiddleware: Add security headers
   │
5. Authentication: Validate JWT token
   │
6. Session Validation: Check session cache
   │
7. RBAC Check: Verify permissions
   │
8. Rate Limit Check: Token bucket algorithm
   │
9. PII Detection: Scan and redact sensitive data
   │
10. Orchestrator.process_message()
    │
11. Coordinator Agent:
    │  a. ML Router prediction (TF-IDF → LogReg)
    │  b. Keyword rule check (word boundaries)
    │  c. Context rule check
    │  d. Final department selection
    │
12. Specialist Agent:
    │  a. Hybrid RAG retrieval
    │     i.  Semantic search (ChromaDB)
    │     ii. BM25 keyword search
    │     iii. RRF fusion
    │  b. Context formatting
    │  c. LLM answer generation
    │
13. Progress Agent (if task-related):
    │  a. Parse task updates from LLM output
    │  b. Update database
    │
14. Database Logging:
    │  a. Messages table (text + redacted)
    │  b. Routing logs table
    │  c. Agent call logs table
    │
15. AuditMiddleware: Log request completion
    │
16. Return JSON response to user
```

## 3. Security Model

### 3.1 Authentication System

```
┌──────────────────────────────────────────────────────────────┐
│                    JWT Authentication Flow                    │
│                                                               │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐      │
│  │  Login  │ → │ Verify  │ → │ Create  │ → │ Return  │      │
│  │ Request │   │Password │   │ Tokens  │   │ Tokens  │      │
│  └─────────┘   └─────────┘   └─────────┘   └─────────┘      │
│                                                               │
│  Token Configuration:                                         │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ Access Token:                                            │ │
│  │   • Expiry: 30 minutes                                   │ │
│  │   • Contains: user_id, email, user_type, permissions     │ │
│  │   • Algorithm: HS256                                     │ │
│  │                                                          │ │
│  │ Refresh Token:                                           │ │
│  │   • Expiry: 7 days                                       │ │
│  │   • Contains: user_id, session_id, jti (unique ID)       │ │
│  │   • Used for: Token renewal without re-login             │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
│  Password Security:                                           │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ • Algorithm: Bcrypt with auto-salting                    │ │
│  │ • Minimum length: 8 characters                           │ │
│  │ • Account lockout: 5 failed attempts                     │ │
│  │ • Lockout duration: 30 minutes                           │ │
│  └─────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

### 3.2 Role-Based Access Control (RBAC)

```
┌──────────────────────────────────────────────────────────────┐
│                    Role Hierarchy                             │
│                                                               │
│  super_admin ────────────────────────────────────────┐       │
│      │                                                │       │
│      ├── admin ──────────────────────────────┐       │       │
│      │     │                                  │       │       │
│      │     ├── hr_admin                      │       │       │
│      │     │                                  │       │       │
│      │     ├── it_admin                      │       │       │
│      │     │                                  │       │       │
│      │     └── security_admin                │       │       │
│      │                                        │       │       │
│      └── manager ───────────────────┐        │       │       │
│            │                         │        │       │       │
│            ├── employee             │        │       │       │
│            │                         │        │       │       │
│            └── new_hire             │        │       │       │
│                                      │        │       │       │
│  Increasing permissions ─────────────┴────────┴───────┘       │
└──────────────────────────────────────────────────────────────┘
```

**Permission Categories:**

| Category | Permissions |
|----------|-------------|
| Chat | `chat:send`, `chat:read:own`, `chat:read:all` |
| Tasks | `task:read:own`, `task:update:own`, `task:read:all`, `task:update:all`, `task:create`, `task:delete` |
| Users | `user:read:own`, `user:update:own`, `user:read:all`, `user:create`, `user:update:all`, `user:delete` |
| Admin | `admin:dashboard`, `admin:metrics`, `admin:logs`, `admin:audit` |
| System | `system:config`, `system:maintenance` |

**Role-Permission Matrix:**

| Role | Own Resources | All Resources | Admin | System |
|------|---------------|---------------|-------|--------|
| new_hire | ✓ | ✗ | ✗ | ✗ |
| employee | ✓ | ✗ | ✗ | ✗ |
| manager | ✓ | Read | Dashboard | ✗ |
| hr_admin | ✓ | Read/Write | Dashboard, Metrics | ✗ |
| it_admin | ✓ | Read | Dashboard, Logs | Config |
| security_admin | ✓ | Read | Dashboard, Audit | ✗ |
| admin | ✓ | Full | Full | ✗ |
| super_admin | ✓ | Full | Full | Full |

### 3.3 Session Management

```
┌──────────────────────────────────────────────────────────────┐
│                    Session Architecture                       │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                  Session Cache                        │    │
│  │                                                       │    │
│  │  Implementation: In-memory TTL cache                  │    │
│  │                                                       │    │
│  │  Key: session_id (32 bytes, URL-safe)                │    │
│  │                                                       │    │
│  │  Value: {                                             │    │
│  │    user_id: int,                                      │    │
│  │    user_name: str,                                    │    │
│  │    user_email: str,                                   │    │
│  │    user_type: str,                                    │    │
│  │    permissions: List[str],                            │    │
│  │    created_at: datetime,                              │    │
│  │    last_activity: datetime,                           │    │
│  │    ip_address: str,                                   │    │
│  │    user_agent: str,                                   │    │
│  │    refresh_token_hash: str (SHA-256)                  │    │
│  │  }                                                    │    │
│  │                                                       │    │
│  │  TTL: 7 days (refresh token expiry)                   │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                               │
│  Session Operations:                                          │
│  • Create: On successful login                                │
│  • Read: On each authenticated request                        │
│  • Update: last_activity on each request                      │
│  • Delete: On logout                                          │
│  • Delete All: On password change                             │
└──────────────────────────────────────────────────────────────┘
```

### 3.4 PII Handling

```
┌──────────────────────────────────────────────────────────────┐
│                    PII Detection Patterns                     │
│                                                               │
│  Pattern                          Example                     │
│  ─────────────────────────────────────────────────────────── │
│  Email addresses                  user@company.com            │
│  Phone numbers (US)               (555) 123-4567              │
│  SSN                              123-45-6789                 │
│  Credit cards                     4111-1111-1111-1111         │
│  IP addresses                     192.168.1.1                 │
│  Names (via NER - optional)       John Smith                  │
└──────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────┐
│                    Redaction Strategy                         │
│                                                               │
│  1. Original text stored in secure column (encrypted)        │
│  2. Redacted version stored separately for logs              │
│  3. PII replaced with <REDACTED> markers                     │
│  4. Audit log entry created for each detection               │
│  5. Metrics counter incremented                               │
└──────────────────────────────────────────────────────────────┘
```

### 3.5 Rate Limiting

**Token Bucket Algorithm:**

```
┌──────────────────────────────────────────────────────────────┐
│                    Token Bucket Rate Limiter                  │
│                                                               │
│  Configuration per user type:                                 │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ User Type    │ Tokens/min │ Burst Size │ Refill Rate    │ │
│  │──────────────│────────────│────────────│────────────────│ │
│  │ new_hire     │    120     │     30     │ 2/sec          │ │
│  │ admin        │    300     │     50     │ 5/sec          │ │
│  │ api          │    180     │     40     │ 3/sec          │ │
│  │ default      │    100     │     25     │ 1.67/sec       │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
│  Behavior:                                                    │
│  • Tokens consumed on each request                            │
│  • Refilled at constant rate                                  │
│  • Burst allows temporary spikes                              │
│  • 429 response when exhausted                                │
│  • Retry-After header included                                │
│                                                               │
│  Exempt Paths:                                                │
│  • /health                                                    │
│  • /metrics                                                   │
│  • /docs                                                      │
└──────────────────────────────────────────────────────────────┘
```

## 4. Audit Logging

### 4.1 Audit Event Categories

```
┌──────────────────────────────────────────────────────────────┐
│                    Audit Event Types                          │
│                                                               │
│  Authentication Events:                                       │
│  ├── auth.login          - Successful login                  │
│  ├── auth.login_failed   - Failed login attempt              │
│  ├── auth.logout         - User logout                       │
│  ├── auth.logout_all     - All sessions invalidated          │
│  ├── auth.token_refresh  - Token refreshed                   │
│  ├── auth.password_change- Password changed                  │
│  └── auth.register       - New user registered               │
│                                                               │
│  Resource Events:                                             │
│  ├── user.create/read/update/delete                          │
│  ├── task.create/read/update/status_change/delete            │
│  └── chat.send/receive                                        │
│                                                               │
│  Admin Events:                                                │
│  ├── admin.dashboard_view                                    │
│  ├── admin.metrics_view                                      │
│  ├── admin.audit_view                                        │
│  └── admin.logs_view                                         │
│                                                               │
│  Security Events:                                             │
│  ├── security.pii_detected                                   │
│  ├── security.rate_limit                                     │
│  └── security.access_denied                                  │
└──────────────────────────────────────────────────────────────┘
```

### 4.2 Audit Log Structure

```json
{
    "id": 12345,
    "timestamp": "2024-01-15T10:30:00Z",
    "action": "chat.send",
    "resource_type": "message",
    "resource_id": 456,
    "user_id": 1,
    "user_email": "alex@company.com",
    "session_id": "HwpjSWd5-W1Qja...",
    "ip_address": "192.168.1.100",
    "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)...",
    "details": {
        "request_id": "req_abc123",
        "method": "POST",
        "path": "/api/v1/chat",
        "status_code": 200,
        "duration_ms": 1234.5,
        "query_params": {}
    },
    "status": "success",
    "error_message": null
}
```

### 4.3 Audit Retention & Compliance

- **Default retention**: 90 days
- **Configurable** via `AUDIT_LOG_RETENTION_DAYS` environment variable
- **Automatic cleanup** of expired logs (scheduled task)
- **Export capability** for compliance audits (JSON, CSV)
- **Immutable** - audit logs cannot be modified once written

## 5. MLOps Approach

### 5.1 Experiment Tracking

```
MLflow Tracking Server (./mlruns)
├── Experiments
│   └── onboarding_router (ID: 521868954883326715)
│       ├── Run: e6adfe3c... (FINISHED)
│       │   ├── Parameters
│       │   │   ├── C: 1.0
│       │   │   ├── max_features: 5000
│       │   │   ├── ngram_range: (1, 2)
│       │   │   └── class_weight: balanced
│       │   ├── Metrics
│       │   │   ├── accuracy: 0.95
│       │   │   ├── f1_macro: 0.94
│       │   │   ├── precision_macro: 0.95
│       │   │   └── recall_macro: 0.93
│       │   └── Artifacts
│       │       ├── model/ (sklearn pipeline)
│       │       └── question_router_labels.json
│       └── Run N: ...
└── Model Registry
    └── question_router
        └── Version 1 (Production)
```

### 5.2 Metrics Collected

**Model Training Metrics:**
| Metric | Description |
|--------|-------------|
| `accuracy` | Overall classification accuracy |
| `f1_macro` | Macro-averaged F1 score |
| `f1_weighted` | Weighted F1 score |
| `precision_macro` | Macro-averaged precision |
| `recall_macro` | Macro-averaged recall |
| `accuracy_{class}` | Per-class accuracy |

**System Metrics (Prometheus):**
| Metric | Type | Labels |
|--------|------|--------|
| `http_requests_total` | Counter | method, endpoint, status_code |
| `http_request_duration_seconds` | Histogram | method, endpoint |
| `routing_predictions_total` | Counter | predicted_dept, final_dept, overridden |
| `rag_retrieval_duration_seconds` | Histogram | - |
| `rag_documents_retrieved_count` | Histogram | - |
| `agent_calls_total` | Counter | agent_name, status |
| `pii_detected_total` | Counter | pii_type |
| `rate_limit_exceeded_total` | Counter | user_id |

### 5.3 Model Lifecycle

```
┌─────────────────────────────────────────────────────────────┐
│                    Model Lifecycle                           │
│                                                              │
│  1. Data Collection                                          │
│     └── data/routing_dataset.json                           │
│         • 150+ labeled examples                              │
│         • 5 department categories                            │
│                                                              │
│  2. Training                                                 │
│     └── python -m ml.training                               │
│         • TF-IDF vectorization                               │
│         • Logistic Regression with CV                        │
│         • Hyperparameter tuning                              │
│                                                              │
│  3. Evaluation                                               │
│     └── Test set metrics                                     │
│         • Accuracy threshold: >70%                           │
│         • Confusion matrix analysis                          │
│         • Per-class performance review                       │
│                                                              │
│  4. Registration                                             │
│     └── MLflow model registry                               │
│         • Version tagging                                    │
│         • Stage transitions (None → Staging → Production)    │
│                                                              │
│  5. Deployment                                               │
│     └── Load from MLflow or fallback to joblib              │
│         • Hot-reload capability                              │
│         • Version tracking in logs                           │
│                                                              │
│  6. Monitoring                                               │
│     └── Prediction distribution tracking                     │
│         • Department distribution over time                  │
│         • Confidence score trends                            │
│         • Override rate monitoring                           │
└─────────────────────────────────────────────────────────────┘
```

## 6. Monitoring Strategy

### 6.1 Application Monitoring

```
Metrics Collection Architecture
├── Request Metrics
│   ├── Count (total, per endpoint, per status)
│   ├── Latency (histogram: p50, p95, p99)
│   └── Error rate (4xx, 5xx)
├── Auth Metrics
│   ├── Login success/failure count
│   ├── Token refresh count
│   ├── Active sessions gauge
│   └── Failed login attempts
├── Agent Metrics
│   ├── Invocation count per agent
│   ├── Processing time histogram
│   └── Error count per agent
├── RAG Metrics
│   ├── Retrieval time histogram
│   ├── Documents retrieved histogram
│   ├── Cache hit/miss ratio
│   └── Confidence score distribution
└── Security Metrics
    ├── PII detections by type
    ├── Rate limit hits
    └── Access denied events
```

### 6.2 Logging Strategy

**Structured JSON Logs (structlog):**

```python
{
    "timestamp": "2024-01-15T10:30:00.123456Z",
    "level": "info",
    "logger": "app.agents.orchestrator",
    "event": "chat_request_processed",
    "user_id": 1,
    "session_id": "abc123",
    "request_id": "req_xyz",
    "department": "HR",
    "router_confidence": 0.92,
    "was_overridden": false,
    "retrieval_time_ms": 45.2,
    "llm_time_ms": 890.5,
    "total_time_ms": 1234.7,
    "sources_count": 3
}
```

**Log Levels:**
- `DEBUG`: Detailed diagnostic information
- `INFO`: Normal operational events
- `WARNING`: Unexpected but handled situations
- `ERROR`: Errors that need attention
- `CRITICAL`: System failures

## 7. Deployment

### 7.1 Local Development

```bash
# Backend (port 8000)
python -m app.main

# Frontend (port 3000)
cd ui && npm run dev

# MLflow UI (port 5001)
mlflow ui --backend-store-uri ./mlruns --port 5001
```

### 7.2 Docker Deployment

```yaml
# docker-compose.yml
services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - SECRET_KEY=${SECRET_KEY}
    volumes:
      - ./data:/app/data
      - ./mlruns:/app/mlruns
    
  frontend:
    build: ./ui
    ports:
      - "3000:3000"
    depends_on:
      - backend
    
  mlflow:
    image: ghcr.io/mlflow/mlflow
    ports:
      - "5001:5000"
    volumes:
      - ./mlruns:/mlruns
    profiles:
      - full
```

### 7.3 Production Considerations

| Component | Development | Production Recommendation |
|-----------|-------------|---------------------------|
| Database | SQLite | PostgreSQL |
| Session Cache | In-memory | Redis |
| Vector Store | ChromaDB (local) | Pinecone, Weaviate |
| Rate Limiter | In-memory | Redis |
| Orchestration | Docker Compose | Kubernetes |
| Monitoring | Prometheus (pull) | Prometheus + Grafana |
| Logging | Console | ELK Stack, Datadog |
| Secrets | .env file | HashiCorp Vault |
| Auth | JWT (internal) | OAuth2/OIDC |
| CDN | - | CloudFront, Cloudflare |

## 8. Future Enhancements

### 8.1 Security
- OAuth2/OIDC integration (SSO)
- Multi-factor authentication (TOTP, WebAuthn)
- API key management for service accounts
- Security event alerting (SIEM integration)
- IP whitelisting and geoblocking

### 8.2 AI/ML
- Fine-tune embedding model on domain data
- Semantic re-ranking with cross-encoders
- Feedback loop for routing model retraining
- Query expansion and spell correction
- Conversation summarization

### 8.3 Features
- Voice interface (speech-to-text, text-to-speech)
- Multi-language support (i18n)
- Calendar integration for task deadlines
- Slack/Teams integration
- Interactive training modules

### 8.4 MLOps
- Automated retraining pipeline
- A/B testing framework
- Data drift detection
- Model performance monitoring
- Shadow deployments

### 8.5 Scalability
- Horizontal scaling with load balancer
- Async processing for heavy operations (Celery)
- Distributed session caching (Redis Cluster)
- Query result caching
- Database read replicas
