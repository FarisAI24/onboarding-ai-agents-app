# Features and Limitations

## Enterprise Onboarding Copilot - Complete Feature Documentation

---

## Table of Contents

1. [Core Features](#1-core-features)
2. [Enhanced Features](#2-enhanced-features)
3. [Administrative Features](#3-administrative-features)
4. [Technical Features](#4-technical-features)
5. [Known Limitations](#5-known-limitations)
6. [Future Improvements](#6-future-improvements)
7. [Complete System Architecture](#7-complete-system-architecture)

---

## 1. Core Features

### 1.1 AI-Powered Chat Assistant

| Feature | Description | Status |
|---------|-------------|--------|
| **Natural Language Understanding** | Understands employee questions in natural language | ✅ Implemented |
| **Multi-Department Support** | Routes queries to HR, IT, Security, Finance agents | ✅ Implemented |
| **Contextual Responses** | Uses RAG to provide accurate, policy-based answers | ✅ Implemented |
| **Source Attribution** | Shows which documents/sections answers come from | ✅ Implemented |
| **Markdown Rendering** | Displays formatted responses with lists, headers, bold | ✅ Implemented |
| **Chat History** | Maintains conversation context within session | ✅ Implemented |

**Example Interactions:**
```
User: "How do I set up VPN?"
Bot: To set up VPN, follow these steps:
     1. Download GlobalProtect VPN client from IT portal
     2. Use your Okta credentials to authenticate
     3. Connect to vpn.company.com
     4. Complete MFA verification
     
     Sources: it_policies.md • 3.1 VPN Configuration
```

---

### 1.2 Onboarding Task Management

| Feature | Description | Status |
|---------|-------------|--------|
| **Task Checklist** | Department-organized task list for new hires | ✅ Implemented |
| **Status Tracking** | NOT_STARTED → IN_PROGRESS → DONE workflow | ✅ Implemented |
| **Due Dates** | Each task has assigned deadline | ✅ Implemented |
| **Overdue Detection** | Automatically flags overdue tasks | ✅ Implemented |
| **Progress Percentage** | Real-time completion percentage | ✅ Implemented |
| **Department Filtering** | Filter tasks by HR, IT, Security, Finance | ✅ Implemented |

**Default Onboarding Tasks:**

| Department | Tasks |
|------------|-------|
| **HR** | HR orientation, Employee handbook, W-4/I-9 forms, Direct deposit, Benefits enrollment |
| **IT** | Laptop setup, Email/calendar, MFA setup, Software installation, VPN configuration |
| **Security** | NDA signing, Security Awareness training, Data Protection training, Phishing Prevention training |
| **Finance** | Expensify account, Expense policy review, Concur travel profile |

---

### 1.3 RAG (Retrieval-Augmented Generation)

| Feature | Description | Status |
|---------|-------------|--------|
| **Hybrid Search** | Combines semantic + keyword (BM25) search | ✅ Implemented |
| **Reciprocal Rank Fusion** | Merges results from multiple retrieval methods | ✅ Implemented |
| **Confidence Scoring** | Rates answer confidence based on retrieval quality | ✅ Implemented |
| **Multi-Document Support** | Searches across all policy documents | ✅ Implemented |
| **Chunk Optimization** | 500-token chunks with 100-token overlap | ✅ Implemented |

**Policy Documents:**
- `hr_policies.md` - Employee benefits, leave, onboarding
- `it_policies.md` - Equipment, VPN, accounts, security
- `security_policies.md` - Compliance, training, access control
- `finance_policies.md` - Expenses, travel, reimbursement

---

### 1.4 Multi-Agent System

| Feature | Description | Status |
|---------|-------------|--------|
| **Coordinator Agent** | Routes queries to appropriate department agent | ✅ Implemented |
| **HR Agent** | Handles benefits, policies, leave questions | ✅ Implemented |
| **IT Agent** | Handles technical support, equipment, accounts | ✅ Implemented |
| **Security Agent** | Handles compliance, training, access questions | ✅ Implemented |
| **Finance Agent** | Handles expenses, payroll, reimbursement | ✅ Implemented |
| **Progress Agent** | Handles task updates, progress queries | ✅ Implemented |
| **LangGraph Orchestration** | State machine for agent coordination | ✅ Implemented |

---

### 1.5 ML-Based Query Routing

| Feature | Description | Status |
|---------|-------------|--------|
| **TF-IDF Vectorization** | Converts queries to numerical features | ✅ Implemented |
| **Logistic Regression** | Classifies queries into departments | ✅ Implemented |
| **Confidence Scoring** | Provides classification confidence | ✅ Implemented |
| **MLflow Tracking** | Logs model experiments and metrics | ✅ Implemented |
| **Model Registry** | Versioned model storage | ✅ Implemented |

---

## 2. Enhanced Features

### 2.1 Multi-Intent Detection

| Feature | Description | Status |
|---------|-------------|--------|
| **Multi-Department Queries** | Detects queries spanning multiple topics | ✅ Implemented |
| **Parallel Agent Processing** | Queries multiple agents simultaneously | ✅ Implemented |
| **Response Combination** | Merges responses from multiple agents | ✅ Implemented |
| **Intent Classification** | Identifies question, task, greeting, etc. | ✅ Implemented |

**Example:**
```
User: "How do I set up VPN and what are my health benefits?"

Bot: **IT Information:**
     To set up VPN, follow these steps...
     
     ---
     
     **HR Information:**
     As a full-time employee, you are eligible for:
     - Basic Plan: $500 deductible
     - Standard Plan: $250 deductible
     - Premium Plan: $100 deductible
```

---

### 2.2 Semantic Caching

| Feature | Description | Status |
|---------|-------------|--------|
| **Exact Match Cache** | O(1) lookup for identical queries | ✅ Implemented |
| **Semantic Similarity Cache** | Finds similar cached queries (≥92% match) | ✅ Implemented |
| **TTL Expiration** | Cache entries expire after 24 hours | ✅ Implemented |
| **Hit Counting** | Tracks cache usage statistics | ✅ Implemented |
| **Cache Invalidation** | Admin can clear cache by department | ✅ Implemented |

**Performance Impact:**
- First query: ~5-8 seconds (LLM call)
- Cached query: ~50-100ms (cache hit)

---

### 2.3 Query Rewriting

| Feature | Description | Status |
|---------|-------------|--------|
| **Spell Correction** | Fixes common typos | ✅ Implemented |
| **Abbreviation Expansion** | Expands "vpn" → "VPN", "pto" → "PTO" | ✅ Implemented |
| **Query Normalization** | Standardizes query format | ✅ Implemented |

**Examples:**
```
"hw do i rquest pto?"     → "how do I request PTO?"
"whats the passwrd rule?" → "what's the password rule?"
```

---

### 2.4 Confidence-Based Escalation

| Feature | Description | Status |
|---------|-------------|--------|
| **Low Confidence Detection** | Flags queries with <30% routing confidence | ✅ Implemented |
| **Escalation Notice** | Adds notice to contact human support | ✅ Implemented |
| **Escalation Logging** | Records escalated queries for review | ✅ Implemented |

---

### 2.5 Gamification & Achievements

| Feature | Description | Status |
|---------|-------------|--------|
| **Achievement System** | Unlockable achievements for milestones | ✅ Implemented |
| **Point System** | Points awarded for achievements | ✅ Implemented |
| **Leaderboard** | Ranks users by total points | ✅ Implemented |
| **Progress Tracking** | Shows locked/unlocked achievements | ✅ Implemented |

**Available Achievements:**

| Achievement | Criteria | Points |
|-------------|----------|--------|
| 🎯 First Task | Complete first task | 10 |
| 📋 HR Champion | Complete all HR tasks | 50 |
| 💻 IT Pro | Complete all IT tasks | 50 |
| 🔒 Security Expert | Complete all security tasks | 50 |
| 💰 Finance Guru | Complete all finance tasks | 50 |
| 🏆 Onboarding Complete | Complete ALL tasks | 100 |
| ❓ Curious Mind | Ask first question | 5 |
| 🔟 Inquisitive | Ask 10 questions | 25 |
| 🎓 Graduate | Complete all training | 75 |
| 🔥 3-Day Streak | Log in 3 consecutive days | 15 |
| 🔥 Week Warrior | Log in 7 consecutive days | 35 |
| 🔥 Monthly Master | Log in 30 consecutive days | 100 |

---

### 2.6 Training & Learning Modules

| Feature | Description | Status |
|---------|-------------|--------|
| **Interactive Modules** | Self-paced training content | ✅ Implemented |
| **Quizzes** | Knowledge verification tests | ✅ Implemented |
| **Progress Tracking** | Tracks module completion | ✅ Implemented |
| **Pass/Fail Scoring** | 80% threshold for completion | ✅ Implemented |

**Available Modules:**

| Module | Duration | Quiz Questions |
|--------|----------|----------------|
| Company Culture | 30 min | 5 |
| Security Basics | 45 min | 10 |
| IT Systems | 30 min | 8 |
| HR Policies | 20 min | 6 |

---

### 2.7 Workflow Automation

| Feature | Description | Status |
|---------|-------------|--------|
| **Event Triggers** | Automated actions on events | ✅ Implemented |
| **Welcome Workflow** | Auto-runs on user registration | ✅ Implemented |
| **Completion Celebration** | Triggers when all tasks done | ✅ Implemented |
| **Deadline Reminders** | Notifications for approaching due dates | ✅ Implemented |
| **Overdue Alerts** | Escalation for missed deadlines | ✅ Implemented |

---

### 2.8 Churn Prediction

| Feature | Description | Status |
|---------|-------------|--------|
| **Engagement Scoring** | Calculates user engagement metrics | ✅ Implemented |
| **Risk Classification** | LOW / MEDIUM / HIGH risk levels | ✅ Implemented |
| **At-Risk User Alerts** | Dashboard shows at-risk users | ✅ Implemented |
| **Intervention Suggestions** | Recommends actions for HR | ✅ Implemented |

**Risk Factors:**
- Login frequency
- Task completion rate
- Chat engagement
- Training progress
- Days since last activity

---

### 2.9 Feedback System

| Feature | Description | Status |
|---------|-------------|--------|
| **Thumbs Up/Down** | Simple response rating | ✅ Implemented |
| **Optional Comments** | Detailed feedback text | ✅ Implemented |
| **Statistics Dashboard** | Feedback analytics | ✅ Implemented |
| **Resolution Tracking** | Mark feedback as addressed | ✅ Implemented |

---

### 2.10 Calendar Integration

| Feature | Description | Status |
|---------|-------------|--------|
| **Event Creation** | Create calendar events | ✅ Implemented |
| **Task Sync** | Sync task deadlines to calendar | ✅ Implemented |
| **ICS Export** | Export to standard calendar format | ✅ Implemented |
| **Event Types** | Meeting, deadline, reminder | ✅ Implemented |
| **Week View** | Calendar week view display | ✅ Implemented |
| **Month View** | Calendar month view display | ✅ Implemented |
| **Event Reminders** | Configurable reminder times | ✅ Implemented |
| **Google Calendar** | OAuth integration (code ready) | 🔮 Future-Ready |
| **Outlook Calendar** | MSAL integration (code ready) | 🔮 Future-Ready |

**Note:** External calendar integration (Google/Outlook) code is fully written and commented out in `app/services/external_calendar_integration.py`. To enable, configure OAuth credentials and uncomment the code.

---

### 2.11 Internationalization (i18n)

| Feature | Description | Status |
|---------|-------------|--------|
| **English Support** | Full English UI | ✅ Implemented |
| **Arabic Support** | Full Arabic UI with RTL | ✅ Implemented |
| **Language Switcher** | UI component for switching | ✅ Implemented |
| **User Preference** | Persisted language preference | ✅ Implemented |

---

## 3. Administrative Features

### 3.1 Authentication & Authorization

| Feature | Description | Status |
|---------|-------------|--------|
| **JWT Authentication** | Secure token-based auth | ✅ Implemented |
| **Role-Based Access Control** | 5-tier role hierarchy | ✅ Implemented |
| **Password Hashing** | bcrypt encryption | ✅ Implemented |
| **Account Lockout** | After 5 failed attempts | ✅ Implemented |
| **Session Management** | Token refresh, logout | ✅ Implemented |

**User Roles:**

| Role | Capabilities |
|------|--------------|
| SUPER_ADMIN | Full system access |
| HR_ADMIN | User management, HR FAQs |
| IT_ADMIN | IT FAQs, system logs |
| MANAGER | Team view, reports |
| NEW_HIRE | Self data, chat, tasks |

---

### 3.2 FAQ Management Portal

| Feature | Description | Status |
|---------|-------------|--------|
| **Create FAQ** | Add new FAQ entries | ✅ Implemented |
| **Edit FAQ** | Modify existing FAQs | ✅ Implemented |
| **Delete FAQ** | Remove FAQs | ✅ Implemented |
| **Categorization** | Organize by department | ✅ Implemented |
| **Publishing Control** | Draft/published states | ✅ Implemented |

---

### 3.3 Audit Log Explorer

| Feature | Description | Status |
|---------|-------------|--------|
| **Log Viewing** | Browse all audit logs with pagination | ✅ Implemented |
| **Filtering** | Filter by action, user ID, date range | ✅ Implemented |
| **Export CSV** | Download logs as CSV file | ✅ Implemented |
| **Summary Cards** | Total events, success/failure counts | ✅ Implemented |
| **Chat Query Display** | Shows user's original question in table | ✅ Implemented |
| **AI Response Display** | Shows AI response in detail modal | ✅ Implemented |
| **Department Tracking** | Shows which department handled query | ✅ Implemented |
| **Detail Modal** | Click row for full query/response view | ✅ Implemented |
| **User Attribution** | Shows user email for each log entry | ✅ Implemented |

---

### 3.4 Admin Dashboard

| Feature | Description | Status |
|---------|-------------|--------|
| **User Progress Overview** | All users' completion status | ✅ Implemented |
| **Aggregate Metrics** | System-wide statistics | ✅ Implemented |
| **Department Analytics** | Completion by department | ✅ Implemented |
| **At-Risk Users List** | Churn prediction alerts | ✅ Implemented |
| **Query Analytics** | Chat usage by department | ✅ Implemented |

---

## 4. Technical Features

### 4.1 Security

| Feature | Description | Status |
|---------|-------------|--------|
| **PII Detection** | Identifies sensitive data | ✅ Implemented |
| **PII Redaction** | Masks sensitive data in logs | ✅ Implemented |
| **Rate Limiting** | 100 requests/minute per user | ✅ Implemented |
| **Security Headers** | CORS, CSP, XSS protection | ✅ Implemented |
| **Input Validation** | Pydantic schema validation | ✅ Implemented |

---

### 4.2 Monitoring

| Feature | Description | Status |
|---------|-------------|--------|
| **Prometheus Metrics** | Standard metrics format | ✅ Implemented |
| **Health Checks** | /health endpoint | ✅ Implemented |
| **Request Logging** | All API requests logged | ✅ Implemented |
| **Error Tracking** | Detailed error logs | ✅ Implemented |
| **Performance Metrics** | Response time tracking | ✅ Implemented |

---

### 4.3 API

| Feature | Description | Status |
|---------|-------------|--------|
| **RESTful Design** | Standard REST endpoints | ✅ Implemented |
| **OpenAPI Docs** | Swagger UI at /docs | ✅ Implemented |
| **Versioned API** | /api/v1/ prefix | ✅ Implemented |
| **JSON Responses** | Consistent response format | ✅ Implemented |

---

## 5. Known Limitations

### 5.1 Technical Limitations

| Limitation | Description | Impact | Workaround |
|------------|-------------|--------|------------|
| **SQLite Database** | Single-file database, not suitable for high concurrency | Medium | Migrate to PostgreSQL for production |
| **In-Memory Embeddings** | ChromaDB stores in local directory | Medium | Use cloud vector store for scale |
| **Single Instance** | No horizontal scaling built-in | Medium | Deploy with load balancer |
| **No Real Email** | Email workflows are simulated | Low | Integrate SMTP service |
| **No Push Notifications** | Browser-only notifications | Low | Add WebSocket/Push API |

---

### 5.2 Feature Limitations

| Limitation | Description | Planned Fix |
|------------|-------------|-------------|
| **English-Only LLM** | AI responses always in English | Prompt engineering for multilingual |
| **No Document Upload** | Policies are pre-loaded files | Add document upload API |
| **Basic Spell Correction** | Rule-based, not ML-based | Integrate LanguageTool API |
| **No Voice Input** | Text-only interface | Add speech-to-text |
| **No Mobile App** | Web-only interface | Create React Native app |
| **Calendar OAuth Disabled** | External calendar code ready but disabled | Configure OAuth credentials to enable |

---

### 5.3 Security Limitations

| Limitation | Description | Recommendation |
|------------|-------------|----------------|
| **JWT in LocalStorage** | Vulnerable to XSS | Use HttpOnly cookies |
| **No 2FA** | Single-factor authentication | Add TOTP/SMS 2FA |
| **No Encryption at Rest** | SQLite not encrypted | Use SQLCipher |
| **Self-Signed SSL** | No production certificates | Use Let's Encrypt |

---

## 6. Future Improvements

### 6.1 Short-Term (1-3 months)

- [ ] PostgreSQL migration for production
- [ ] Real email integration (SendGrid/SES)
- [x] Google Calendar OAuth integration (code ready, needs credentials)
- [x] Microsoft Outlook OAuth integration (code ready, needs credentials)
- [ ] Two-factor authentication
- [ ] Advanced spell correction (LanguageTool)
- [ ] Document upload for policies

### 6.2 Medium-Term (3-6 months)

- [ ] Mobile app (React Native)
- [ ] Voice input/output
- [ ] Slack/Teams integration
- [ ] Advanced analytics dashboard
- [ ] A/B testing for responses
- [ ] Custom workflow builder UI

### 6.3 Long-Term (6-12 months)

- [ ] Multi-tenant architecture
- [ ] Custom LLM fine-tuning
- [ ] Video onboarding modules
- [ ] Virtual mentor matching
- [ ] Predictive task scheduling
- [ ] Integration marketplace

---

## 7. Complete System Architecture

### 7.1 High-Level Overview

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                                  │
│                           ENTERPRISE ONBOARDING COPILOT                                         │
│                                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────┐│
│  │                                    PRESENTATION LAYER                                        ││
│  │                                                                                              ││
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐    ││
│  │  │   Chat Interface │  │   Task Manager   │  │  Training Portal │  │  Admin Dashboard │    ││
│  │  │                  │  │                  │  │                  │  │                  │    ││
│  │  │ • Message input  │  │ • Task list      │  │ • Modules        │  │ • User management│    ││
│  │  │ • Response view  │  │ • Status toggle  │  │ • Quizzes        │  │ • FAQ CRUD       │    ││
│  │  │ • Feedback       │  │ • Progress bar   │  │ • Progress       │  │ • Audit logs     │    ││
│  │  │ • FAQ shortcuts  │  │ • Filters        │  │ • Certificates   │  │ • Analytics      │    ││
│  │  └──────────────────┘  └──────────────────┘  └──────────────────┘  └──────────────────┘    ││
│  │                                                                                              ││
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐                          ││
│  │  │   Achievements   │  │ Language Switcher│  │   Leaderboard    │                          ││
│  │  │                  │  │                  │  │                  │                          ││
│  │  │ • Badge display  │  │ • EN / AR        │  │ • User ranking   │                          ││
│  │  │ • Points         │  │ • RTL support    │  │ • Points display │                          ││
│  │  └──────────────────┘  └──────────────────┘  └──────────────────┘                          ││
│  │                                                                                              ││
│  │                              Next.js 14 + React 18 + TailwindCSS                            ││
│  └─────────────────────────────────────────────────────────────────────────────────────────────┘│
│                                              │                                                   │
│                                              ▼                                                   │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────┐│
│  │                                      API GATEWAY                                             ││
│  │                                                                                              ││
│  │  ┌──────────────────────────────────────────────────────────────────────────────────────┐  ││
│  │  │                               FastAPI Application                                     │  ││
│  │  │                                                                                       │  ││
│  │  │  ┌────────────────────────────────────────────────────────────────────────────────┐ │  ││
│  │  │  │  MIDDLEWARE STACK                                                               │ │  ││
│  │  │  │                                                                                 │ │  ││
│  │  │  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐              │ │  ││
│  │  │  │  │   CORS      │ │ Rate Limit  │ │ Auth Check  │ │ PII Redact  │              │ │  ││
│  │  │  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘              │ │  ││
│  │  │  │                                                                                 │ │  ││
│  │  │  └────────────────────────────────────────────────────────────────────────────────┘ │  ││
│  │  │                                                                                       │  ││
│  │  │  ┌────────────────────────────────────────────────────────────────────────────────┐ │  ││
│  │  │  │  API ROUTES                                                                     │ │  ││
│  │  │  │                                                                                 │ │  ││
│  │  │  │  /api/v1/auth/*      - Authentication endpoints                                │ │  ││
│  │  │  │  /api/v1/chat        - Chat endpoint                                           │ │  ││
│  │  │  │  /api/v1/tasks/*     - Task management                                         │ │  ││
│  │  │  │  /api/v1/users/*     - User management                                         │ │  ││
│  │  │  │  /api/v1/training/*  - Training modules                                        │ │  ││
│  │  │  │  /api/v1/achievements/*- Gamification                                          │ │  ││
│  │  │  │  /api/v1/feedback/*  - Feedback system                                         │ │  ││
│  │  │  │  /api/v1/faqs/*      - FAQ management                                          │ │  ││
│  │  │  │  /api/v1/calendar/*  - Calendar integration                                    │ │  ││
│  │  │  │  /api/v1/workflows/* - Workflow automation                                     │ │  ││
│  │  │  │  /api/v1/i18n/*      - Internationalization                                    │ │  ││
│  │  │  │  /api/v1/admin/*     - Admin endpoints                                         │ │  ││
│  │  │  │  /api/v1/audit/*     - Audit logs                                              │ │  ││
│  │  │  │  /api/v1/churn/*     - Churn prediction                                        │ │  ││
│  │  │  │  /api/v1/health      - Health check                                            │ │  ││
│  │  │  │  /api/v1/metrics     - Prometheus metrics                                      │ │  ││
│  │  │  │                                                                                 │ │  ││
│  │  │  └────────────────────────────────────────────────────────────────────────────────┘ │  ││
│  │  │                                                                                       │  ││
│  │  └──────────────────────────────────────────────────────────────────────────────────────┘  ││
│  │                                                                                              ││
│  └─────────────────────────────────────────────────────────────────────────────────────────────┘│
│                                              │                                                   │
│                                              ▼                                                   │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────┐│
│  │                                    SERVICE LAYER                                             ││
│  │                                                                                              ││
│  │  ┌────────────────────────────────────────────────────────────────────────────────────────┐││
│  │  │                              QUERY PROCESSING PIPELINE                                  │││
│  │  │                                                                                         │││
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │││
│  │  │  │   Query     │  │  Semantic   │  │   Intent    │  │    ML       │  │ Confidence  │ │││
│  │  │  │  Rewriting  │─►│   Cache     │─►│  Detection  │─►│  Routing    │─►│ Escalation  │ │││
│  │  │  │             │  │   Check     │  │             │  │             │  │   Check     │ │││
│  │  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘ │││
│  │  │                                                                                         │││
│  │  └────────────────────────────────────────────────────────────────────────────────────────┘││
│  │                                              │                                              ││
│  │                                              ▼                                              ││
│  │  ┌────────────────────────────────────────────────────────────────────────────────────────┐││
│  │  │                              MULTI-AGENT SYSTEM (LangGraph)                             │││
│  │  │                                                                                         │││
│  │  │                          ┌───────────────────────────────┐                             │││
│  │  │                          │      COORDINATOR AGENT        │                             │││
│  │  │                          │                               │                             │││
│  │  │                          │  • Query analysis             │                             │││
│  │  │                          │  • Department routing         │                             │││
│  │  │                          │  • Multi-intent detection     │                             │││
│  │  │                          └───────────────┬───────────────┘                             │││
│  │  │                                          │                                              │││
│  │  │          ┌───────────────┬───────────────┼───────────────┬───────────────┐             │││
│  │  │          │               │               │               │               │             │││
│  │  │          ▼               ▼               ▼               ▼               ▼             │││
│  │  │    ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐          │││
│  │  │    │    HR    │   │    IT    │   │ Security │   │ Finance  │   │ Progress │          │││
│  │  │    │  Agent   │   │  Agent   │   │  Agent   │   │  Agent   │   │  Agent   │          │││
│  │  │    │          │   │          │   │          │   │          │   │          │          │││
│  │  │    │ Benefits │   │Equipment │   │Compliance│   │ Expenses │   │  Tasks   │          │││
│  │  │    │ Policies │   │ Accounts │   │ Training │   │ Payroll  │   │ Updates  │          │││
│  │  │    │  Leave   │   │   VPN    │   │ Security │   │  Travel  │   │ Status   │          │││
│  │  │    └────┬─────┘   └────┬─────┘   └────┬─────┘   └────┬─────┘   └────┬─────┘          │││
│  │  │         │              │              │              │              │                │││
│  │  │         └──────────────┴──────────────┼──────────────┴──────────────┘                │││
│  │  │                                       │                                              │││
│  │  │                          ┌────────────▼────────────┐                                 │││
│  │  │                          │    RESPONSE COMBINER    │                                 │││
│  │  │                          │                         │                                 │││
│  │  │                          │  • Multi-agent merge    │                                 │││
│  │  │                          │  • Format response      │                                 │││
│  │  │                          │  • Source attribution   │                                 │││
│  │  │                          └─────────────────────────┘                                 │││
│  │  │                                                                                         │││
│  │  └────────────────────────────────────────────────────────────────────────────────────────┘││
│  │                                              │                                              ││
│  │                                              ▼                                              ││
│  │  ┌────────────────────────────────────────────────────────────────────────────────────────┐││
│  │  │                                  RAG SYSTEM                                             │││
│  │  │                                                                                         │││
│  │  │  ┌─────────────────────────────────────────────────────────────────────────────────┐  │││
│  │  │  │                            HYBRID RETRIEVER                                      │  │││
│  │  │  │                                                                                  │  │││
│  │  │  │  ┌──────────────────────────┐    ┌──────────────────────────┐                  │  │││
│  │  │  │  │   SEMANTIC SEARCH        │    │    KEYWORD SEARCH        │                  │  │││
│  │  │  │  │                          │    │                          │                  │  │││
│  │  │  │  │  HuggingFace             │    │    BM25 Algorithm        │                  │  │││
│  │  │  │  │  all-mpnet-base-v2       │    │                          │                  │  │││
│  │  │  │  │  (768 dimensions)        │    │                          │                  │  │││
│  │  │  │  │                          │    │                          │                  │  │││
│  │  │  │  └────────────┬─────────────┘    └────────────┬─────────────┘                  │  │││
│  │  │  │               │                               │                                │  │││
│  │  │  │               └───────────────┬───────────────┘                                │  │││
│  │  │  │                               │                                                │  │││
│  │  │  │                    ┌──────────▼──────────┐                                     │  │││
│  │  │  │                    │ Reciprocal Rank     │                                     │  │││
│  │  │  │                    │ Fusion (RRF)        │                                     │  │││
│  │  │  │                    └──────────┬──────────┘                                     │  │││
│  │  │  │                               │                                                │  │││
│  │  │  └───────────────────────────────┼────────────────────────────────────────────────┘  │││
│  │  │                                  │                                                    │││
│  │  │                       ┌──────────▼──────────┐                                        │││
│  │  │                       │   CONTEXT BUILDER   │                                        │││
│  │  │                       │                     │                                        │││
│  │  │                       │  • Top-K chunks     │                                        │││
│  │  │                       │  • Confidence score │                                        │││
│  │  │                       │  • Source metadata  │                                        │││
│  │  │                       └──────────┬──────────┘                                        │││
│  │  │                                  │                                                    │││
│  │  │                       ┌──────────▼──────────┐                                        │││
│  │  │                       │    LLM GENERATOR    │                                        │││
│  │  │                       │                     │                                        │││
│  │  │                       │   OpenAI gpt-4o-mini│                                        │││
│  │  │                       │   Temperature: 0.3 │                                        │││
│  │  │                       └─────────────────────┘                                        │││
│  │  │                                                                                         │││
│  │  └────────────────────────────────────────────────────────────────────────────────────────┘││
│  │                                                                                              ││
│  │  ┌────────────────────────────────────────────────────────────────────────────────────────┐││
│  │  │                              SUPPORT SERVICES                                           │││
│  │  │                                                                                         │││
│  │  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐      │││
│  │  │  │Achievement  │ │ Training    │ │ Workflow    │ │  Churn      │ │ Calendar    │      │││
│  │  │  │ Service     │ │ Service     │ │ Service     │ │ Prediction  │ │ Service     │      │││
│  │  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘      │││
│  │  │                                                                                         │││
│  │  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐      │││
│  │  │  │ Feedback    │ │ FAQ         │ │ i18n        │ │ Audit       │ │ Semantic    │      │││
│  │  │  │ Service     │ │ Service     │ │ Service     │ │ Service     │ │ Cache       │      │││
│  │  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘      │││
│  │  │                                                                                         │││
│  │  └────────────────────────────────────────────────────────────────────────────────────────┘││
│  │                                                                                              ││
│  └─────────────────────────────────────────────────────────────────────────────────────────────┘│
│                                              │                                                   │
│                                              ▼                                                   │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────┐│
│  │                                      DATA LAYER                                              ││
│  │                                                                                              ││
│  │  ┌──────────────────────────────────┐  ┌──────────────────────────────────┐                ││
│  │  │           SQLite                  │  │          ChromaDB                 │                ││
│  │  │                                   │  │                                   │                ││
│  │  │  ┌─────────────────────────────┐ │  │  ┌─────────────────────────────┐ │                ││
│  │  │  │ users                       │ │  │  │ Policy Documents            │ │                ││
│  │  │  │ tasks                       │ │  │  │                             │ │                ││
│  │  │  │ messages                    │ │  │  │ • hr_policies.md            │ │                ││
│  │  │  │ sessions                    │ │  │  │ • it_policies.md            │ │                ││
│  │  │  │ audit_logs                  │ │  │  │ • security_policies.md      │ │                ││
│  │  │  │ routing_logs                │ │  │  │ • finance_policies.md       │ │                ││
│  │  │  │ feedback                    │ │  │  │                             │ │                ││
│  │  │  │ semantic_cache              │ │  │  │ Embeddings: 768-dim vectors │ │                ││
│  │  │  │ achievements                │ │  │  │ Chunks: 500 tokens          │ │                ││
│  │  │  │ user_achievements           │ │  │  │ Overlap: 100 tokens         │ │                ││
│  │  │  │ training_modules            │ │  │  │                             │ │                ││
│  │  │  │ training_progress           │ │  │  └─────────────────────────────┘ │                ││
│  │  │  │ workflows                   │ │  │                                   │                ││
│  │  │  │ workflow_executions         │ │  └──────────────────────────────────┘                ││
│  │  │  │ calendar_events             │ │                                                       ││
│  │  │  │ faqs                        │ │  ┌──────────────────────────────────┐                ││
│  │  │  │ engagement_metrics          │ │  │          MLflow                   │                ││
│  │  │  │ churn_predictions           │ │  │                                   │                ││
│  │  │  │                             │ │  │  • Experiment tracking            │                ││
│  │  │  └─────────────────────────────┘ │  │  • Model registry                 │                ││
│  │  │                                   │  │  • Routing model versions         │                ││
│  │  └──────────────────────────────────┘  │                                   │                ││
│  │                                         └──────────────────────────────────┘                ││
│  │                                                                                              ││
│  └─────────────────────────────────────────────────────────────────────────────────────────────┘│
│                                              │                                                   │
│                                              ▼                                                   │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────┐│
│  │                                   MONITORING LAYER                                           ││
│  │                                                                                              ││
│  │  ┌──────────────────────────────────┐  ┌──────────────────────────────────┐                ││
│  │  │        Prometheus Metrics         │  │         Application Logs          │                ││
│  │  │                                   │  │                                   │                ││
│  │  │  • http_requests_total           │  │  • Request/response logging       │                ││
│  │  │  • http_request_duration_seconds │  │  • Error tracking                  │                ││
│  │  │  • chat_messages_total           │  │  • Agent decisions                 │                ││
│  │  │  • task_completions_total        │  │  • RAG retrieval stats            │                ││
│  │  │  • rag_retrievals_total          │  │  • Cache hit/miss                  │                ││
│  │  │  • cache_hits_total              │  │                                   │                ││
│  │  │                                   │  │                                   │                ││
│  │  └──────────────────────────────────┘  └──────────────────────────────────┘                ││
│  │                                                                                              ││
│  └─────────────────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

### 7.2 Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                      DATA FLOW                                                   │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘

                                    ┌─────────────┐
                                    │    USER     │
                                    └──────┬──────┘
                                           │
                          ┌────────────────┼────────────────┐
                          │                │                │
                          ▼                ▼                ▼
                    ┌──────────┐     ┌──────────┐     ┌──────────┐
                    │   Chat   │     │  Tasks   │     │ Training │
                    │  Query   │     │  Update  │     │  Quiz    │
                    └────┬─────┘     └────┬─────┘     └────┬─────┘
                         │                │                │
                         ▼                │                │
            ┌────────────────────────┐    │                │
            │  Query Processing      │    │                │
            │  Pipeline              │    │                │
            │                        │    │                │
            │  1. Spell correction   │    │                │
            │  2. Cache check        │    │                │
            │  3. Intent detection   │    │                │
            │  4. ML routing         │    │                │
            └───────────┬────────────┘    │                │
                        │                 │                │
           ┌────────────┴────────────┐    │                │
           │                         │    │                │
           ▼                         ▼    │                │
    ┌─────────────┐           ┌──────────┴───────────────┴────┐
    │ Cache HIT   │           │       Multi-Agent System       │
    │             │           │                                │
    │ Return      │           │  ┌──────┐ ┌──────┐ ┌──────┐  │
    │ cached      │           │  │  HR  │ │  IT  │ │ Sec  │  │
    │ response    │           │  └──┬───┘ └──┬───┘ └──┬───┘  │
    └──────┬──────┘           │     │        │        │      │
           │                  │     ▼        ▼        ▼      │
           │                  │  ┌────────────────────────┐  │
           │                  │  │    RAG Pipeline        │  │
           │                  │  │                        │  │
           │                  │  │  ChromaDB → Context   │  │
           │                  │  │  Context → LLM        │  │
           │                  │  │  LLM → Response       │  │
           │                  │  └───────────┬────────────┘  │
           │                  │              │               │
           │                  └──────────────┼───────────────┘
           │                                 │
           │                                 ▼
           │                  ┌──────────────────────────────┐
           │                  │      Post-Processing         │
           │                  │                              │
           │                  │  • Cache response            │
           │                  │  • Check achievements        │
           │                  │  • Trigger workflows         │
           │                  │  • Log to audit              │
           │                  └──────────────┬───────────────┘
           │                                 │
           └─────────────────┬───────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   Database      │
                    │   Updates       │
                    │                 │
                    │  • messages     │
                    │  • routing_logs │
                    │  • cache        │
                    │  • achievements │
                    │  • audit_logs   │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │    Response     │
                    │    to User      │
                    └─────────────────┘
```

---

### 7.3 Component Summary

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Frontend** | Next.js 14, React 18, TailwindCSS | User interface |
| **API Server** | FastAPI, Python 3.11+ | RESTful API |
| **AI Orchestration** | LangGraph | Multi-agent coordination |
| **LLM** | OpenAI gpt-4o-mini | Response generation |
| **Embeddings** | HuggingFace all-mpnet-base-v2 | Semantic search |
| **Vector Store** | ChromaDB | Document retrieval |
| **Database** | SQLite | Structured data |
| **ML Pipeline** | Scikit-learn, MLflow | Query routing |
| **Monitoring** | Prometheus | Metrics collection |
| **Authentication** | JWT, bcrypt | Security |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | Dec 2024 | Initial release with core features |
| 1.1.0 | Dec 2024 | Added authentication, RBAC, audit logging |
| 1.2.0 | Dec 2024 | Added 13 enhanced features (gamification, training, etc.) |
| 1.3.0 | Dec 2024 | Multi-intent detection, semantic caching |
| 1.4.0 | Dec 2024 | Full i18n context, calendar OAuth ready, robustness fixes |
| 1.5.0 | Dec 2024 | Enhanced audit logging with full chat details, user creation API fix, comprehensive documentation |

---

## Related Documentation

| Document | Description |
|----------|-------------|
| [TECHNICAL_REPORT.md](TECHNICAL_REPORT.md) | Comprehensive technical report with implementation details |
| [SYSTEM_ARCHITECTURES.md](SYSTEM_ARCHITECTURES.md) | Detailed architecture diagrams for all systems |
| [README.md](../README.md) | Quick start guide and overview |