# Enterprise Onboarding Copilot

An AI-powered, multi-agent onboarding assistant that helps new employees navigate company policies, complete onboarding tasks, and get answers to their questions. Features production-grade security with JWT authentication, RBAC, session management, and comprehensive audit logging.

## 🌟 Features

### Core Features
- **💬 Chat-based Assistant**: Natural language Q&A grounded in company policy documents via RAG
- **👥 Role-aware Guidance**: Responses adapted to user's role and department
- **✅ Onboarding Checklist**: Task management with status tracking (NOT_STARTED, IN_PROGRESS, DONE)
- **📊 Progress Tracking**: Visual progress indicators with overdue task highlighting
- **⚡ FAQ Shortcuts**: Quick access to common onboarding topics
- **📈 Admin Dashboard**: Aggregate metrics and user progress monitoring

### Multi-Agent Architecture
- **Coordinator Agent**: Routes queries using ML-based classification + keyword rules
- **HR Agent**: Benefits, PTO, leave policies, employment contracts
- **IT Agent**: Devices, accounts, VPN, email, development tools
- **Security Agent**: Training, compliance, NDAs, access control
- **Finance Agent**: Payroll, expenses, reimbursements, travel
- **Progress Agent**: Task tracking and status updates

### Security & Authentication
- **🔐 JWT Authentication**: Secure token-based auth with access/refresh tokens
- **👮 RBAC**: Role-based access control with 8 roles and 20+ granular permissions
- **📝 Session Management**: User session tracking with activity monitoring
- **🛡️ PII Detection**: Automatic detection and redaction of sensitive data
- **⏱️ Rate Limiting**: Tiered rate limits by user type (token bucket algorithm)
- **📋 Audit Logging**: Comprehensive audit trail for all system actions

### Enhanced Features (v1.4)
- **🏆 Gamification**: Achievement system with points, badges, and leaderboard
- **📚 Training Modules**: Interactive learning with quizzes and progress tracking
- **📅 Calendar Integration**: Internal calendar with ICS export (Google/Outlook OAuth ready)
- **🌍 Internationalization**: Full Arabic/English support with RTL layout
- **🔮 Semantic Caching**: Reduces LLM calls by caching similar queries
- **🎯 Multi-Intent Detection**: Handles queries spanning multiple departments
- **📊 Churn Prediction**: Identifies at-risk users based on engagement
- **⚡ Query Rewriting**: Spell correction and abbreviation expansion

### Technical Highlights
- **Hybrid RAG Pipeline**: Semantic search + BM25 keyword search with Reciprocal Rank Fusion
- **ML Routing**: TF-IDF + Logistic Regression classifier with MLflow tracking
- **LangGraph Orchestration**: State-machine based agent coordination
- **Prometheus Metrics**: Full observability with Prometheus-compatible metrics
- **Structured Logging**: JSON-formatted logs with request correlation

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              Frontend (Next.js 14)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐  │
│  │ Login/Signup │  │   Chat UI    │  │  Task List   │  │ Admin Dash │  │
│  │   (JWT)      │  │  (Markdown)  │  │  (Progress)  │  │ (Metrics)  │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  └────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           FastAPI Backend                                │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                    Security & Middleware Layer                      │ │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐ │ │
│  │  │JWT Auth │  │  RBAC   │  │Rate Lim │  │PII Scan │  │  Audit  │ │ │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘ │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │ /auth        │  │ /chat        │  │ /admin       │                  │
│  └──────────────┘  └──────────────┘  └──────────────┘                  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
┌──────────────────────┐  ┌──────────────┐  ┌──────────────────────┐
│   LangGraph Agent    │  │  ML Router   │  │    Hybrid RAG         │
│   Orchestrator       │  │  (TF-IDF +   │  │  (Semantic + BM25)   │
│                      │  │   LogReg)    │  │                      │
│  ┌─────┐ ┌─────┐    │  └──────────────┘  │  ┌────────┐ ┌──────┐ │
│  │ HR  │ │ IT  │    │                     │  │ChromaDB│ │BM25  │ │
│  └─────┘ └─────┘    │         │           │  └────────┘ └──────┘ │
│  ┌─────┐ ┌─────┐    │         │           │        │             │
│  │Sec. │ │Fin. │    │         ▼           │        ▼             │
│  └─────┘ └─────┘    │  ┌──────────────┐   │  ┌──────────┐        │
│  ┌──────────────┐   │  │   MLflow     │   │  │   RRF    │        │
│  │   Progress   │   │  │   Registry   │   │  │ Reranker │        │
└──────────────────────┘  └──────────────┘   └──────────────────────┘
                                    │
                                    ▼
                          ┌──────────────────┐
                          │     SQLite       │
                          │  ┌────────────┐  │
                          │  │ Users      │  │
                          │  │ Tasks      │  │
                          │  │ Messages   │  │
                          │  │ Sessions   │  │
                          │  │ Audit Logs │  │
                          │  │ Routing    │  │
                          │  └────────────┘  │
                          └──────────────────┘
```

## 📁 Project Structure

```
onboardingAI_agents/
├── app/                          # Backend application
│   ├── agents/                   # Multi-agent system (LangGraph)
│   │   ├── base.py               # Base agent class & state definitions
│   │   ├── coordinator.py        # Routing coordinator with ML + rules
│   │   ├── hr_agent.py           # HR specialist agent
│   │   ├── it_agent.py           # IT specialist agent
│   │   ├── security_agent.py     # Security/compliance agent
│   │   ├── finance_agent.py      # Finance/admin agent
│   │   ├── progress_agent.py     # Task tracking agent
│   │   └── orchestrator.py       # LangGraph workflow orchestrator
│   ├── api/                      # FastAPI routes
│   │   ├── routes.py             # Core API endpoints
│   │   ├── auth_routes.py        # Authentication endpoints
│   │   ├── feature_routes.py     # Enhanced feature endpoints
│   │   ├── schemas.py            # Pydantic request/response models
│   │   └── middleware.py         # Security & metrics middleware
│   ├── auth/                     # Authentication module
│   │   ├── service.py            # JWT token & password handling
│   │   ├── dependencies.py       # FastAPI auth dependencies
│   │   ├── rbac.py               # Role-based access control
│   │   └── schemas.py            # Auth-specific Pydantic models
│   ├── audit/                    # Audit logging module
│   │   ├── service.py            # Audit logger service
│   │   └── middleware.py         # Request/response audit middleware
│   ├── database/                 # Database layer
│   │   ├── models.py             # SQLAlchemy ORM models
│   │   └── connection.py         # Database connection management
│   ├── monitoring/               # Observability
│   │   └── metrics.py            # Prometheus metrics collectors
│   ├── security/                 # Security utilities
│   │   ├── pii_detector.py       # PII detection & redaction
│   │   └── rate_limiter.py       # Token bucket rate limiter
│   ├── services/                 # Business services
│   │   ├── achievements.py       # Gamification & achievements
│   │   ├── training.py           # Training modules & quizzes
│   │   ├── calendar_service.py   # Calendar events
│   │   ├── feedback.py           # User feedback
│   │   ├── faq_service.py        # FAQ management
│   │   ├── semantic_cache.py     # Query caching
│   │   ├── intent_detector.py    # Multi-intent detection
│   │   ├── query_processor.py    # Query rewriting
│   │   ├── churn_prediction.py   # Engagement-based churn
│   │   ├── workflows.py          # Automated workflows
│   │   ├── i18n.py               # Internationalization
│   │   ├── escalation.py         # Confidence escalation
│   │   ├── external_calendar_integration.py  # OAuth calendar (future)
│   │   └── security.py           # Security helper functions
│   ├── config.py                 # Application configuration
│   └── main.py                   # FastAPI app entry point
├── rag/                          # RAG pipeline
│   ├── embeddings.py             # HuggingFace embedding service
│   ├── vectorstore.py            # ChromaDB vector store operations
│   ├── hybrid_search.py          # Hybrid search (semantic + BM25 + RRF)
│   ├── ingestion.py              # Document chunking & processing
│   ├── retriever.py              # RAG retrieval & answer generation
│   └── evaluation.py             # RAG evaluation metrics
├── ml/                           # ML components
│   ├── router.py                 # Question routing classifier
│   ├── training.py               # Model training with MLflow
│   └── mlflow_integration.py     # MLflow utilities
├── ui/                           # Next.js 14 frontend
│   ├── src/
│   │   ├── app/                  # App router
│   │   │   ├── layout.tsx        # Root layout with providers
│   │   │   ├── page.tsx          # Main page with auth flow
│   │   │   ├── providers.tsx     # Client-side providers
│   │   │   └── globals.css       # Global styles
│   │   ├── components/           # React components
│   │   │   ├── LoginForm.tsx     # Login form with validation
│   │   │   ├── RegisterForm.tsx  # Registration form
│   │   │   ├── ChatInterface.tsx # Chat UI with markdown
│   │   │   ├── TaskList.tsx      # Task management UI
│   │   │   ├── AdminDashboard.tsx # Admin metrics dashboard
│   │   │   ├── AchievementsPanel.tsx # Gamification UI
│   │   │   ├── TrainingModules.tsx # Training & quizzes
│   │   │   ├── CalendarView.tsx  # Calendar management
│   │   │   ├── FAQManagement.tsx # Admin FAQ CRUD
│   │   │   ├── ChurnDashboard.tsx # At-risk users
│   │   │   ├── AuditLogExplorer.tsx # Audit log viewer
│   │   │   ├── FeedbackButtons.tsx # Thumbs up/down
│   │   │   └── LanguageSwitcher.tsx # i18n language toggle
│   │   └── lib/                  # Utilities
│   │       ├── api.ts            # API client with auth
│   │       ├── auth-context.tsx  # React auth context
│   │       └── i18n-context.tsx  # Internationalization context
│   ├── tailwind.config.js        # Tailwind configuration
│   ├── package.json              # Node dependencies
│   └── Dockerfile                # Frontend container
├── data/                         # Data directory
│   ├── policies/                 # Policy documents (Markdown)
│   │   ├── hr_policies.md
│   │   ├── it_policies.md
│   │   ├── security_policies.md
│   │   └── finance_policies.md
│   ├── routing_dataset.json      # Training data for ML router
│   ├── chroma_db/                # Vector store (gitignored)
│   ├── models/                   # Trained models (gitignored)
│   └── onboarding.db             # SQLite database (gitignored)
├── scripts/                      # Utility scripts
│   ├── init_system.py            # System initialization
│   ├── evaluate_rag.py           # RAG evaluation runner
│   └── health_check.py           # System health validation
├── docs/                         # Documentation
│   ├── SYSTEM_ARCHITECTURES.md   # Detailed architecture diagrams
│   ├── FEATURES_AND_LIMITATIONS.md # Feature documentation
│   ├── TECHNICAL_REPORT.md       # Comprehensive technical report
│   └── SYSTEM_DESIGN.md          # System design overview
├── mlruns/                       # MLflow experiments (gitignored)
├── docker-compose.yml            # Docker orchestration
├── Dockerfile                    # Backend container
├── requirements.txt              # Python dependencies
├── .gitignore                    # Git ignore rules
└── README.md                     # This file
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+
- OpenAI API key

### Local Development

1. **Clone and setup environment:**
```bash
cd onboardingAI_agents

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

2. **Configure environment:**
```bash
# Create .env file
cat > .env << EOF
OPENAI_API_KEY=your_openai_api_key_here
DATABASE_URL=sqlite:///./data/onboarding.db
CHROMA_PERSIST_DIRECTORY=./data/chroma_db
MLFLOW_TRACKING_URI=./mlruns
SECRET_KEY=your-secure-secret-key-minimum-32-characters
APP_ENV=development
DEBUG=true
EOF
```

3. **Initialize the system:**
```bash
# This will:
# - Create database tables
# - Ingest policy documents into ChromaDB
# - Train the routing model
# - Create demo users
python scripts/init_system.py
```

4. **Start the backend:**
```bash
python -m app.main
# API available at http://localhost:8000
# Docs at http://localhost:8000/docs
```

5. **Start the frontend:**
```bash
cd ui
npm install
npm run dev
# UI available at http://localhost:3000
```

6. **Start MLflow UI (optional):**
```bash
mlflow ui --backend-store-uri ./mlruns --port 5001
# MLflow UI at http://localhost:5001
```

### Docker Deployment

```bash
# Set your OpenAI API key
export OPENAI_API_KEY=your_key_here

# Build and run
docker-compose up --build

# With MLflow UI (optional)
docker-compose --profile full up --build
```

## 🔐 Authentication & Authorization

### User Roles

| Role | Description | Key Permissions |
|------|-------------|-----------------|
| `new_hire` | New employees | Own resources only |
| `employee` | Regular employees | Own resources only |
| `manager` | Team managers | Team resources + dashboard |
| `hr_admin` | HR administrators | User management, all HR data |
| `it_admin` | IT administrators | System config, logs |
| `security_admin` | Security team | Audit logs, security data |
| `admin` | Full administrators | All except system config |
| `super_admin` | Super administrators | Full access |

### Authentication Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/auth/register` | POST | Register new user |
| `/api/v1/auth/login` | POST | Login and get tokens |
| `/api/v1/auth/refresh` | POST | Refresh access token |
| `/api/v1/auth/logout` | POST | Logout (invalidate session) |
| `/api/v1/auth/me` | GET | Get current user info |
| `/api/v1/auth/password/change` | POST | Change password |
| `/api/v1/auth/sessions` | GET | List active sessions |

### Example: Login Flow

```bash
# Register a new user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@company.com",
    "password": "securepassword123",
    "role": "Software Engineer",
    "department": "Engineering"
  }'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@company.com",
    "password": "securepassword123"
  }'

# Response:
# {
#   "access_token": "eyJ...",
#   "refresh_token": "eyJ...",
#   "token_type": "bearer",
#   "expires_in": 1800
# }

# Use access token for protected endpoints
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer eyJ..."
```

### Demo Credentials

After running `init_system.py`:

| Role | Email | Password |
|------|-------|----------|
| Admin | `admin@company.com` | `admin123` |
| New Hire | `alex.chen@company.com` | `password123` |
| New Hire | `sarah.johnson@company.com` | `password123` |

## 📚 API Documentation

### Core Endpoints

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/v1/health` | GET | Health check | No |
| `/api/v1/metrics` | GET | Prometheus metrics | No |
| `/api/v1/chat` | POST | Send a message to the assistant | Yes |
| `/api/v1/tasks` | GET | Get user's onboarding tasks | Yes |
| `/api/v1/tasks/{id}/status` | POST | Update task status | Yes |
| `/api/v1/users/{id}` | GET | Get user with progress | Yes |
| `/api/v1/faq` | GET | Get FAQ topics | No |

### Admin Endpoints

| Endpoint | Method | Description | Required Role |
|----------|--------|-------------|---------------|
| `/api/v1/admin/users` | GET | Get all users progress | admin, hr_admin |
| `/api/v1/admin/metrics` | GET | Get aggregate metrics | admin, manager |
| `/api/v1/admin/audit` | GET | Get audit logs | admin, security_admin |

### Feature Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/achievements` | GET | Get user achievements |
| `/api/v1/achievements/leaderboard` | GET | Get points leaderboard |
| `/api/v1/training/modules` | GET | Get training modules |
| `/api/v1/training/modules/{id}/quiz` | POST | Submit quiz answers |
| `/api/v1/calendar/events` | GET/POST | Manage calendar events |
| `/api/v1/calendar/sync-tasks` | POST | Sync tasks to calendar |
| `/api/v1/calendar/export.ics` | GET | Export ICS file |
| `/api/v1/feedback` | POST | Submit response feedback |
| `/api/v1/faqs` | GET/POST | Manage FAQs |
| `/api/v1/churn/at-risk` | GET | Get at-risk users |
| `/api/v1/i18n/{lang}` | GET | Get translations |
| `/api/v1/audit/logs` | GET | Get audit logs |

### Chat Request Example
```json
POST /api/v1/chat
Authorization: Bearer <access_token>

{
  "user_id": 1,
  "message": "What health insurance options are available?"
}
```

### Response
```json
{
  "response": "Based on our HR policies, we offer three health insurance options...",
  "sources": [
    {"document": "hr_policies.md", "section": "Health Insurance", "department": "HR"}
  ],
  "routing": {
    "predicted_department": "HR",
    "prediction_confidence": 0.92,
    "final_department": "HR",
    "was_overridden": false
  },
  "agent": "hr",
  "total_time_ms": 1234.5
}
```

## 🧪 Testing & Evaluation

### Run System Health Check
```bash
python scripts/health_check.py
```

This validates all system components:
- Public endpoints (health, FAQs, i18n)
- Authentication flow
- Feature endpoints (achievements, training, calendar, etc.)
- Admin endpoints (users, metrics, audit logs)

### Run RAG Evaluation
```bash
python scripts/evaluate_rag.py
```

This evaluates retrieval quality using:
- Hit rate (document found in top-K)
- Mean Reciprocal Rank (MRR)
- Retrieval latency

### Train/Retrain Routing Model
```bash
python -m ml.training --C 1.0 --max-features 5000
```

Training results are logged to MLflow with:
- Accuracy, Precision, Recall, F1 (macro/weighted)
- Per-class metrics
- Confusion matrix
- Feature importances

## 🔒 Security Features

### Authentication
- JWT tokens with configurable expiry (30 min access, 7 days refresh)
- Bcrypt password hashing with automatic salting
- Account lockout after 5 failed login attempts
- Session tracking with activity monitoring

### Authorization
- Role-based access control (RBAC) with 8 roles
- 20+ granular permissions
- Resource-level access checks (own vs. all)

### Data Protection
- **PII Detection**: Emails, phone numbers, SSNs automatically redacted
- **Rate Limiting**: Tiered limits (new_hire: 120/min, admin: 300/min)
- **Security Headers**: CORS, XSS protection, content type sniffing prevention

### Audit Logging
- All authentication events logged
- All resource access logged
- Admin actions tracked
- Security events (rate limits, access denied) recorded
- 90-day retention by default

## 📊 Monitoring

### Service URLs

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | React/Next.js UI |
| Backend API | http://localhost:8000 | FastAPI server |
| API Docs | http://localhost:8000/docs | Swagger/OpenAPI |
| MLflow | http://localhost:5001 | Experiment tracking |

### Prometheus Metrics
- Endpoint: `/api/v1/metrics`
- Request latency histograms
- Request counts by endpoint and status
- Auth success/failure rates
- Rate limit hits
- RAG retrieval statistics

### Key Metrics Tracked
- Request latency (p50, p95, p99)
- Routing predictions by department
- RAG retrieval time and hit rate
- Onboarding completion rates
- Authentication events
- Session statistics

## 🎯 Demo Walkthrough

### New Hire Experience

1. **Open** http://localhost:3000
2. **Login** with demo credentials or register
3. **Ask questions** like:
   - "What health insurance options are available?"
   - "How do I connect to VPN?"
   - "When is security training due?"
   - "How do I submit expenses?"
4. **View tasks** in the Tasks tab
5. **Mark tasks complete** by clicking the status icon
6. **Track progress** with the progress bar

### Admin Experience

1. **Login** with admin account
2. **Admin Dashboard** appears in sidebar (admin roles only)
3. **View aggregate metrics**:
   - Total new hires
   - Average completion percentage
   - Queries by department
4. **Monitor individual progress** in the user table
5. **View audit logs** for security compliance

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| **Backend** | FastAPI, Python 3.11, Pydantic v2 |
| **Frontend** | Next.js 14, React 18, Tailwind CSS |
| **AI/LLM** | OpenAI GPT-4o-mini, LangChain |
| **Multi-Agent** | LangGraph |
| **Embeddings** | HuggingFace `all-mpnet-base-v2` |
| **Vector Store** | ChromaDB |
| **Hybrid Search** | BM25 + Semantic + RRF |
| **ML Pipeline** | scikit-learn, TF-IDF, LogisticRegression |
| **Experiment Tracking** | MLflow |
| **Database** | SQLite (SQLAlchemy ORM) |
| **Authentication** | JWT (python-jose), Bcrypt (passlib) |
| **Logging** | structlog (JSON) |
| **Metrics** | Prometheus client |
| **Containerization** | Docker, docker-compose |

## 📝 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `SECRET_KEY` | JWT signing key | Required |
| `DATABASE_URL` | SQLite connection string | `sqlite:///./data/onboarding.db` |
| `CHROMA_PERSIST_DIRECTORY` | ChromaDB storage path | `./data/chroma_db` |
| `MLFLOW_TRACKING_URI` | MLflow storage path | `./mlruns` |
| `APP_ENV` | Environment (development/production) | `development` |
| `DEBUG` | Enable debug mode | `true` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT access token TTL | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | JWT refresh token TTL | `7` |

### Optional: External Calendar Integration

To enable Google/Outlook calendar sync, add these variables:

```env
# Google Calendar (optional)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/calendar/oauth/google/callback

# Microsoft Outlook (optional)
MICROSOFT_CLIENT_ID=your_microsoft_client_id
MICROSOFT_CLIENT_SECRET=your_microsoft_client_secret
MICROSOFT_REDIRECT_URI=http://localhost:8000/api/v1/calendar/oauth/microsoft/callback
```

Then uncomment the code in `app/services/external_calendar_integration.py`.

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [TECHNICAL_REPORT.md](docs/TECHNICAL_REPORT.md) | Comprehensive technical report with full system details |
| [SYSTEM_ARCHITECTURES.md](docs/SYSTEM_ARCHITECTURES.md) | Detailed architecture diagrams for all 17 systems |
| [FEATURES_AND_LIMITATIONS.md](docs/FEATURES_AND_LIMITATIONS.md) | Complete feature list and known limitations |
| [SYSTEM_DESIGN.md](docs/SYSTEM_DESIGN.md) | High-level system design overview |

## 📄 License

This project is for educational and demonstration purposes.