# Enterprise Onboarding Copilot - Technical Report

## Complete System Documentation & Implementation Guide

**Version:** 1.5.0  
**Date:** December 2024  
**Author:** AI Development Team

---

## Executive Summary

The Enterprise Onboarding Copilot is an AI-powered, multi-agent system designed to streamline employee onboarding. It combines modern AI techniques (RAG, multi-agent orchestration, ML classification) with enterprise-grade security (JWT, RBAC, audit logging) to deliver a comprehensive onboarding assistant.

### Key Metrics

| Metric | Value |
|--------|-------|
| **Response Time (cached)** | ~50-100ms |
| **Response Time (new query)** | ~3-8 seconds |
| **Routing Accuracy** | ~87% (ML + rules) |
| **Supported Languages** | English, Arabic |
| **Active Agents** | 6 specialized agents |
| **Policy Documents** | 4 departments |
| **Achievements Available** | 12 badges |
| **Training Modules** | 4 courses |

---

## Table of Contents

1. [System Architecture Overview](#1-system-architecture-overview)
2. [Technology Stack](#2-technology-stack)
3. [AI/ML Components](#3-aiml-components)
4. [Multi-Agent System](#4-multi-agent-system)
5. [RAG Pipeline](#5-rag-pipeline)
6. [Authentication & Security](#6-authentication--security)
7. [Audit & Logging System](#7-audit--logging-system)
8. [Caching Strategy](#8-caching-strategy)
9. [Database Schema](#9-database-schema)
10. [API Reference](#10-api-reference)
11. [Frontend Architecture](#11-frontend-architecture)
12. [Performance Optimizations](#12-performance-optimizations)
13. [Deployment Guide](#13-deployment-guide)
14. [Testing & Validation](#14-testing--validation)
15. [Known Issues & Limitations](#15-known-issues--limitations)
16. [Future Roadmap](#16-future-roadmap)

---

## 1. System Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PRESENTATION LAYER                                 │
│                     Next.js 14 + React 18 + TailwindCSS                     │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐  │
│  │  Chat   │ │  Tasks  │ │Training │ │Calendar │ │Achieve- │ │  Admin  │  │
│  │Interface│ │  List   │ │ Modules │ │  View   │ │ ments   │ │Dashboard│  │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              API LAYER                                       │
│                      FastAPI + Middleware Stack                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  CORS │ Rate Limit │ JWT Auth │ RBAC │ PII Redact │ Audit Logging   │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  /auth  │  /chat  │  /tasks  │  /training  │  /admin  │  /audit     │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            SERVICE LAYER                                     │
│  ┌────────────────────────────────────────────────────────────────────────┐│
│  │                    QUERY PROCESSING PIPELINE                            ││
│  │  Query Rewrite → Cache Check → Intent Detect → ML Route → Escalation  ││
│  └────────────────────────────────────────────────────────────────────────┘│
│  ┌────────────────────────────────────────────────────────────────────────┐│
│  │                    MULTI-AGENT SYSTEM (LangGraph)                       ││
│  │  Coordinator → [HR | IT | Security | Finance | Progress] → Combine     ││
│  └────────────────────────────────────────────────────────────────────────┘│
│  ┌────────────────────────────────────────────────────────────────────────┐│
│  │                    RAG PIPELINE                                         ││
│  │  Semantic Search (ChromaDB) + BM25 → RRF Fusion → LLM Generation       ││
│  └────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DATA LAYER                                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │     SQLite      │  │    ChromaDB     │  │     MLflow      │             │
│  │  (Structured)   │  │  (Vectors)      │  │  (ML Models)    │             │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Request Flow

1. **User sends query** via frontend
2. **API Gateway** validates JWT, applies rate limiting
3. **Query Processing** rewrites, checks cache, detects intent
4. **ML Router** classifies to department with confidence score
5. **LangGraph** orchestrates appropriate agent(s)
6. **Agent** retrieves context via RAG, generates response
7. **Response** cached, logged to audit, returned to user

---

## 2. Technology Stack

### Backend

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| **Framework** | FastAPI | 0.104+ | REST API server |
| **Python** | Python | 3.11+ | Runtime |
| **ORM** | SQLAlchemy | 2.0+ | Database abstraction |
| **Validation** | Pydantic | 2.0+ | Request/response models |
| **Auth** | python-jose, passlib | Latest | JWT, password hashing |
| **Logging** | structlog | Latest | Structured JSON logs |

### AI/ML

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| **LLM** | OpenAI GPT-4o-mini | Latest | Response generation |
| **Embeddings** | all-mpnet-base-v2 | Latest | 768-dim vectors |
| **Vector Store** | ChromaDB | 0.4+ | Semantic search |
| **Orchestration** | LangGraph | 0.1+ | Multi-agent coordination |
| **ML Pipeline** | scikit-learn | 1.3+ | Query classification |
| **Experiment Tracking** | MLflow | 2.9+ | Model versioning |

### Frontend

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| **Framework** | Next.js | 14 | React framework |
| **UI Library** | React | 18 | Component library |
| **Styling** | TailwindCSS | 3.4+ | Utility-first CSS |
| **Animation** | Framer Motion | 10+ | UI animations |
| **Icons** | Lucide React | Latest | Icon library |

---

## 3. AI/ML Components

### 3.1 Question Router (Classification)

**Architecture:** TF-IDF + Logistic Regression

```python
Pipeline([
    ('tfidf', TfidfVectorizer(
        max_features=5000,
        ngram_range=(1, 2),
        stop_words='english'
    )),
    ('classifier', LogisticRegression(
        C=1.0,
        class_weight='balanced',
        multi_class='multinomial'
    ))
])
```

**Output Classes:** Finance, General, HR, IT, Security

**Override Rules:**
- Keyword matching with word boundaries
- Confidence threshold (0.6) for overrides
- Arabic keyword support for multilingual routing

### 3.2 Embedding Model

**Model:** `sentence-transformers/all-mpnet-base-v2`
- **Dimensions:** 768
- **Architecture:** MPNet (Masked and Permuted Language Model)
- **Caching:** LRU cache with 10,000 entries

### 3.3 Semantic Cache

**Strategy:** Two-tier caching
1. **Exact Match:** SHA-256 hash lookup (O(1))
2. **Semantic Match:** Cosine similarity ≥ 0.92

**TTL:** 24 hours

### 3.4 Churn Prediction

**Algorithm:** Rule-based engagement scoring

```python
WEIGHTS = {
    "task_completion": 0.30,
    "activity_frequency": 0.25,
    "learning_progress": 0.20,
    "chat_engagement": 0.15,
    "feedback_sentiment": 0.10
}
```

**Risk Levels:** LOW (>65), MEDIUM (45-65), HIGH (25-45), CRITICAL (<25)

---

## 4. Multi-Agent System

### Agent Responsibilities

| Agent | Department | Responsibilities |
|-------|------------|------------------|
| **Coordinator** | Routing | Query classification, multi-intent detection |
| **HR Agent** | HR | Benefits, PTO, leave, policies, onboarding |
| **IT Agent** | IT | Equipment, VPN, accounts, software, support |
| **Security Agent** | Security | Compliance, training, NDAs, access control |
| **Finance Agent** | Finance | Expenses, payroll, travel, reimbursements |
| **Progress Agent** | Tasks | Task status, checklist updates, progress |

### LangGraph State Machine

```
Entry Point: coordinator
    │
    ├── HR Route     → hr_agent     → finalize → END
    ├── IT Route     → it_agent     → finalize → END
    ├── Security     → security_agent → finalize → END
    ├── Finance      → finance_agent → finalize → END
    ├── Progress     → progress_agent → finalize → END
    └── Multi-Intent → [agent1, agent2] → combine → END
```

### Multi-Intent Handling

When a query spans multiple departments:
1. Intent detector identifies all relevant departments
2. Query routed to each agent in parallel
3. Responses combined with section headers
4. Combined response returned to user

---

## 5. RAG Pipeline

### Hybrid Retrieval

```
User Query
    │
    ├── Semantic Search (ChromaDB)
    │   └── Embed query → Vector similarity → Top-K
    │
    └── Keyword Search (BM25)
        └── Tokenize → TF-IDF scoring → Top-K
    │
    ▼
Reciprocal Rank Fusion (RRF)
    │
    ▼
Combined Score = 0.7 × Semantic + 0.3 × BM25
    │
    ▼
Top-5 Document Chunks → Context
    │
    ▼
LLM Generation (GPT-4o-mini)
```

### Configuration

| Parameter | Value |
|-----------|-------|
| Chunk Size | 500 tokens |
| Chunk Overlap | 100 tokens |
| Top-K Retrieval | 5 documents |
| Semantic Weight | 0.7 |
| BM25 Weight | 0.3 |
| Cache TTL | 30 minutes |

---

## 6. Authentication & Security

### JWT Token Structure

```json
{
  "sub": "user_id",
  "email": "user@company.com",
  "user_type": "new_hire",
  "session_id": "unique_session_id",
  "permissions": ["chat:send", "task:update:own"],
  "exp": 1234567890,
  "type": "access"
}
```

### Role Hierarchy

| Role | Level | Permissions |
|------|-------|-------------|
| super_admin | 5 | Full system access |
| admin | 4 | All except system config |
| hr_admin | 3 | User management, HR data |
| it_admin | 3 | IT FAQs, system logs |
| manager | 2 | Team view, reports |
| employee | 1 | Own resources |
| new_hire | 0 | Basic access |

### Security Features

- **Password Hashing:** bcrypt with automatic salting
- **Account Lockout:** 5 failed attempts → 30 min lock
- **Rate Limiting:** Token bucket algorithm (100 req/min default)
- **PII Detection:** Regex-based detection and redaction
- **Security Headers:** CORS, XSS protection, CSP

---

## 7. Audit & Logging System

### Audit Log Structure

```sql
CREATE TABLE audit_logs (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME,
    action VARCHAR(100),      -- auth.login, chat.send, etc.
    resource_type VARCHAR(50), -- user, message, task, etc.
    resource_id INTEGER,
    user_id INTEGER,
    user_email VARCHAR(255),
    session_id VARCHAR(255),
    ip_address VARCHAR(45),
    user_agent TEXT,
    details JSON,             -- Full context data
    status VARCHAR(20),       -- success, failure, error
    error_message TEXT
);
```

### Chat Audit Details

For `chat.send` actions, the `details` JSON contains:

```json
{
  "query": "What is the PTO policy?",
  "response": "The PTO policy allows employees to...",
  "department": "HR",
  "predicted_department": "HR",
  "confidence": 0.87,
  "agent": "hr",
  "duration_ms": 4523.5
}
```

### Audit Explorer Features

- Summary cards (total events, success/failure counts)
- Filterable table (action, user, date range)
- Query/response display columns
- Detail modal for full context
- CSV export functionality

---

## 8. Caching Strategy

### Multi-Level Caching

| Cache Level | Technology | TTL | Purpose |
|-------------|------------|-----|---------|
| **Embedding Cache** | LRU (in-memory) | Session | Avoid recomputing embeddings |
| **Hybrid Search Cache** | TTLCache | 30 min | Store search results |
| **Semantic Query Cache** | SQLite | 24 hours | Cache LLM responses |
| **Session Cache** | In-memory | 60 min | User session data |

### Cache Performance

| Scenario | Response Time |
|----------|---------------|
| Exact cache hit | ~50ms |
| Semantic cache hit | ~100ms |
| Cache miss (full pipeline) | ~3-8 seconds |

---

## 9. Database Schema

### Core Tables

| Table | Description |
|-------|-------------|
| `users` | User accounts with roles |
| `tasks` | Onboarding tasks |
| `messages` | Chat history |
| `feedback` | User feedback on responses |
| `achievements` | Available achievements |
| `user_achievements` | Unlocked achievements |
| `training_modules` | Training content |
| `training_progress` | User progress |
| `calendar_events` | Calendar entries |
| `workflows` | Automated workflows |
| `audit_logs` | Comprehensive audit trail |
| `routing_logs` | ML routing decisions |
| `semantic_cache` | Cached query/responses |

---

## 10. API Reference

### Core Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/v1/health` | GET | No | Health check |
| `/api/v1/auth/login` | POST | No | User login |
| `/api/v1/auth/register` | POST | No | User registration |
| `/api/v1/chat` | POST | Yes | Send chat message |
| `/api/v1/tasks` | GET | Yes | Get user tasks |
| `/api/v1/tasks/{id}/status` | POST | Yes | Update task status |

### Feature Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/v1/achievements` | GET | Yes | User achievements |
| `/api/v1/training/modules` | GET | Yes | Training modules |
| `/api/v1/calendar/events` | GET/POST | Yes | Calendar management |
| `/api/v1/feedback` | POST | Yes | Submit feedback |
| `/api/v1/i18n/{lang}` | GET | No | Get translations |

### Admin Endpoints

| Endpoint | Method | Role Required | Description |
|----------|--------|---------------|-------------|
| `/api/v1/admin/users` | GET | admin, hr_admin | All users |
| `/api/v1/admin/metrics` | GET | admin, manager | Aggregate metrics |
| `/api/v1/audit/logs` | GET | admin | Audit logs |
| `/api/v1/churn/at-risk` | GET | admin, manager | At-risk users |

---

## 11. Frontend Architecture

### Component Structure

```
ui/src/
├── app/
│   ├── layout.tsx          # Root layout with providers
│   ├── page.tsx            # Main page with routing
│   └── providers.tsx       # Context providers
├── components/
│   ├── ChatInterface.tsx   # Chat with AI
│   ├── TaskList.tsx        # Task management
│   ├── AchievementsPanel.tsx # Gamification
│   ├── TrainingModules.tsx # Learning system
│   ├── CalendarView.tsx    # Calendar
│   ├── AuditLogExplorer.tsx # Admin audit logs
│   ├── ChurnDashboard.tsx  # At-risk users
│   └── FeedbackButtons.tsx # Response feedback
└── lib/
    ├── api.ts              # API client
    ├── auth-context.tsx    # Authentication context
    └── i18n-context.tsx    # Internationalization
```

### Key Features

- **Fixed Chat Container:** Scrollable messages with fixed input
- **Dark/Light Text:** High contrast for readability
- **RTL Support:** Full Arabic language support
- **Responsive Design:** Mobile-friendly layouts

---

## 12. Performance Optimizations

### Backend Optimizations

| Optimization | Implementation | Impact |
|--------------|----------------|--------|
| **Parallel DB Queries** | `asyncio.gather` | -40% latency |
| **Background Tasks** | `ThreadPoolExecutor` | Non-blocking saves |
| **Embedding Cache** | LRU cache (10K entries) | -80% embedding time |
| **Parallel Search** | Concurrent semantic + BM25 | -30% search time |
| **Preloading** | Startup initialization | Faster first request |

### Frontend Optimizations

| Optimization | Implementation |
|--------------|----------------|
| **State Lifting** | Chat messages persist across tabs |
| **Lazy Loading** | Components load on demand |
| **Debounced Input** | Reduced API calls |

---

## 13. Deployment Guide

### Local Development

```bash
# Backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python scripts/init_system.py
python -m app.main

# Frontend
cd ui && npm install && npm run dev

# MLflow
mlflow ui --port 5001
```

### Docker Deployment

```bash
docker-compose up --build
```

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes | - | OpenAI API key |
| `SECRET_KEY` | Yes | - | JWT signing key |
| `DATABASE_URL` | No | sqlite:///./data/onboarding.db | Database connection |
| `DEBUG` | No | true | Debug mode |

---

## 14. Testing & Validation

### Health Check Script

```bash
python scripts/health_check.py
```

Validates:
- All API endpoints responding
- Authentication flow working
- Database connectivity
- ML model loading

### RAG Evaluation

```bash
python scripts/evaluate_rag.py
```

Measures:
- Hit rate (document found in top-K)
- Mean Reciprocal Rank (MRR)
- Retrieval latency

---

## 15. Known Issues & Limitations

| Limitation | Impact | Workaround |
|------------|--------|------------|
| SQLite (single-file) | Medium | Migrate to PostgreSQL for production |
| No real email sending | Low | Integrate SMTP service |
| No push notifications | Low | Add WebSocket support |
| External calendar OAuth disabled | Low | Configure credentials to enable |

---

## 16. Future Roadmap

### Short-Term (1-3 months)
- [ ] PostgreSQL migration
- [ ] Real email integration
- [x] External calendar OAuth (code ready)
- [ ] Two-factor authentication

### Medium-Term (3-6 months)
- [ ] Mobile app (React Native)
- [ ] Slack/Teams integration
- [ ] Advanced analytics
- [ ] Custom workflow builder

### Long-Term (6-12 months)
- [ ] Multi-tenant architecture
- [ ] Custom LLM fine-tuning
- [ ] Video onboarding modules
- [ ] Integration marketplace

---

## References

- **System Architectures:** See `docs/SYSTEM_ARCHITECTURES.md`
- **Features & Limitations:** See `docs/FEATURES_AND_LIMITATIONS.md`
- **API Documentation:** Available at `http://localhost:8000/docs`
- **README:** See `README.md` for quick start guide

---

*This document provides a comprehensive technical overview of the Enterprise Onboarding Copilot system. For specific implementation details, refer to the source code and inline documentation.*

