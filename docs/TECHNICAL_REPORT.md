# Enterprise Onboarding Copilot - Technical Report

## Complete System Documentation & Implementation Guide

**Version:** 1.0.2
**Date:** December 2025  
**Author:** Faris Alzayed
**Document Type:** Comprehensive Technical Report

---

## Executive Summary

The Enterprise Onboarding Copilot is a production-grade, AI-powered multi-agent system designed to revolutionize employee onboarding processes. Built with modern AI techniques including Retrieval-Augmented Generation (RAG), multi-agent orchestration via LangGraph, and ML-based query classification, the system provides intelligent, context-aware assistance to new hires while maintaining enterprise-grade security through JWT authentication, Role-Based Access Control (RBAC), and comprehensive audit logging.

### System Highlights

- **Intelligent Query Routing**: ML-powered classification (TF-IDF + Logistic Regression) routes queries to specialized department agents with ~87% accuracy
- **Hybrid RAG Pipeline**: Combines semantic search (ChromaDB + SentenceTransformers) with keyword search (BM25) using Reciprocal Rank Fusion for optimal retrieval
- **Multi-Agent Architecture**: 6 specialized agents (Coordinator, HR, IT, Security, Finance, Progress) orchestrated via LangGraph state machine
- **Multilingual Support**: Full English and Arabic language support with RTL UI, automatic language detection, and Arabic-to-English query translation for RAG
- **Gamification Engine**: 12 achievement badges, points system, and leaderboard to encourage engagement
- **Predictive Analytics**: Rule-based churn prediction with engagement scoring and proactive intervention recommendations

### Key Performance Metrics

| Metric | Value | Notes |
|--------|-------|-------|
| **Response Time (exact cache hit)** | ~50ms | SHA-256 hash lookup |
| **Response Time (semantic cache hit)** | ~100ms | Cosine similarity ≥0.92 |
| **Response Time (full pipeline)** | 3-8 seconds | Including LLM generation |
| **ML Routing Accuracy** | ~87% | With keyword override rules |
| **Semantic Cache Threshold** | 0.92 | Cosine similarity |
| **Hybrid Search Cache TTL** | 30 minutes | TTLCache with 5000 entries |
| **Embedding Cache Size** | 10,000 entries | LRU in-memory cache |
| **Supported Languages** | 2 | English, Arabic |
| **Specialized Agents** | 6 | HR, IT, Security, Finance, Progress, Coordinator |
| **Policy Documents** | 4 departments | HR, IT, Security, Finance |
| **Achievement Badges** | 12 | Across 5 categories |
| **Training Modules** | 4 courses | With quizzes |
| **Database Tables** | 18 | SQLite with SQLAlchemy ORM |

---

## Table of Contents

1. [System Architecture Overview](#1-system-architecture-overview)
2. [Technology Stack](#2-technology-stack)
3. [AI/ML Components](#3-aiml-components)
4. [Multi-Agent System](#4-multi-agent-system)
5. [RAG Pipeline](#5-rag-pipeline)
6. [Query Processing Pipeline](#6-query-processing-pipeline)
7. [Authentication & Security](#7-authentication--security)
8. [Audit & Logging System](#8-audit--logging-system)
9. [Caching Strategy](#9-caching-strategy)
10. [Database Schema](#10-database-schema)
11. [Gamification & Achievements](#11-gamification--achievements)
12. [Churn Prediction System](#12-churn-prediction-system)
13. [Feedback System](#13-feedback-system)
14. [Internationalization (i18n)](#14-internationalization-i18n)
15. [API Reference](#15-api-reference)
16. [Frontend Architecture](#16-frontend-architecture)
17. [Performance Optimizations](#17-performance-optimizations)
18. [Deployment Guide](#18-deployment-guide)
19. [Testing & Validation](#19-testing--validation)
20. [Known Issues & Limitations](#20-known-issues--limitations)
21. [Future Roadmap](#21-future-roadmap)
22. [Appendices](#22-appendices)

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

### Backend Technologies

| Layer | Component | Technology | Version | Purpose |
|-------|-----------|------------|---------|---------|
| **Framework** | Web Server | FastAPI | 0.104+ | Async REST API |
| **Runtime** | Language | Python | 3.11+ | Backend runtime |
| **Database** | ORM | SQLAlchemy | 2.0+ | Database abstraction |
| **Database** | Engine | SQLite | 3.x | Development database |
| **Validation** | Schema | Pydantic | 2.0+ | Request/response validation |
| **Auth** | JWT | python-jose | Latest | Token generation/validation |
| **Auth** | Password | passlib[bcrypt] | Latest | Password hashing |
| **Logging** | Structured | structlog | Latest | JSON formatted logs |
| **Async** | Concurrency | asyncio, ThreadPoolExecutor | Built-in | Parallel execution |
| **Caching** | TTL Cache | cachetools | Latest | In-memory caching |

### AI/ML Technologies

| Layer | Component | Technology | Version | Purpose |
|-------|-----------|------------|---------|---------|
| **LLM** | Generation | OpenAI GPT-4o-mini | Latest | Response generation |
| **Embeddings** | Model | all-mpnet-base-v2 | Latest | 768-dimensional vectors |
| **Vector Store** | Database | ChromaDB | 0.4+ | Semantic search storage |
| **Orchestration** | Multi-Agent | LangGraph | 0.1+ | State machine orchestration |
| **Classification** | ML Pipeline | scikit-learn | 1.3+ | TF-IDF + LogisticRegression |
| **Keyword Search** | BM25 | rank_bm25 | Latest | Keyword-based retrieval |
| **Tracking** | MLOps | MLflow | 2.9+ | Experiment tracking, model registry |
| **Metrics** | Evaluation | numpy | Latest | Numerical computations |

### Frontend Technologies

| Layer | Component | Technology | Version | Purpose |
|-------|-----------|------------|---------|---------|
| **Framework** | Meta-Framework | Next.js | 14 | React framework with SSR |
| **UI** | Library | React | 18 | Component-based UI |
| **Styling** | CSS | TailwindCSS | 3.4+ | Utility-first styling |
| **Animation** | Motion | Framer Motion | 10+ | Smooth animations |
| **Icons** | Graphics | Lucide React | Latest | SVG icon library |
| **State** | Management | React Context | Built-in | Global state |
| **HTTP** | Client | Fetch API | Built-in | API communication |

### Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND                                  │
│                     (Next.js 14)                                │
│                                                                  │
│  React Components → API Client → HTTP Fetch                     │
└──────────────────────────────┬──────────────────────────────────┘
                               │ REST API
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                         BACKEND                                  │
│                       (FastAPI)                                  │
│                                                                  │
│  Middleware → Routes → Services → Agents → RAG → LLM           │
└──────────────────────────────┬──────────────────────────────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
        ▼                      ▼                      ▼
┌───────────────┐    ┌─────────────────┐    ┌───────────────┐
│    SQLite     │    │    ChromaDB     │    │    MLflow     │
│ (Structured)  │    │   (Vectors)     │    │  (ML Models)  │
│               │    │                 │    │               │
│ - Users       │    │ - Embeddings    │    │ - Router      │
│ - Tasks       │    │ - Documents     │    │ - Experiments │
│ - Messages    │    │ - Metadata      │    │ - Metrics     │
│ - Audit Logs  │    │                 │    │               │
└───────────────┘    └─────────────────┘    └───────────────┘
```

---

## 3. AI/ML Components

### 3.1 Question Router (Classification Model)

**Purpose:** Classify incoming user queries to the appropriate department for routing to specialized agents.

**Architecture:** Classical ML Pipeline (TF-IDF + Logistic Regression)

**Implementation:** `ml/router.py` and `ml/training.py`

```python
Pipeline([
    ('tfidf', TfidfVectorizer(
        max_features=5000,           # Vocabulary size limit
        ngram_range=(1, 2),          # Unigrams and bigrams
        stop_words='english',        # Remove common words
        lowercase=True,              # Case normalization
        strip_accents='unicode'      # Handle accented characters
    )),
    ('classifier', LogisticRegression(
        C=1.0,                       # Regularization strength
        max_iter=1000,               # Convergence iterations
        class_weight='balanced',     # Handle class imbalance
        multi_class='multinomial',   # Multi-class strategy
        solver='lbfgs',              # Optimization algorithm
        random_state=42              # Reproducibility
    ))
])
```

**Output Classes:** `["Finance", "General", "HR", "IT", "Security"]`

**Model Outputs:**
- `department`: Predicted department string
- `confidence`: Probability score (0.0-1.0)
- `all_probabilities`: Dict of all class probabilities

**Training Data:** `data/routing_dataset.json` - Custom labeled dataset with query-department pairs

**MLflow Integration:**
- Experiment tracking at `mlruns/`
- Model versioning and registration
- Metrics logging (accuracy, precision, recall, F1)

**Override Rules (Keyword Matching):**
The ML prediction can be overridden by keyword matching for higher accuracy:

| Department | English Keywords | Arabic Keywords |
|------------|-----------------|-----------------|
| HR | benefit, insurance, health, pto, vacation, leave, policy | تأمين, صحي, إجازة, مزايا, موارد بشرية |
| IT | vpn, laptop, email, password, software, account | كمبيوتر, حاسوب, لابتوب, بريد, كلمة مرور |
| Security | security, training, compliance, badge, nda | أمن, تدريب, بطاقة, سرية |
| Finance | expense, payroll, reimburse, tax, budget, travel | راتب, مصاريف, نفقات, ضريبة |

### 3.2 Embedding Model (Deep Learning)

**Purpose:** Generate 768-dimensional dense vector representations of text for semantic search and similarity matching.

**Model:** `sentence-transformers/all-mpnet-base-v2`

**Implementation:** `rag/embeddings.py`

| Property | Value |
|----------|-------|
| **Architecture** | MPNet (Masked and Permuted Pre-training) |
| **Output Dimensions** | 768 |
| **Max Sequence Length** | 384 tokens |
| **Training Corpus** | 1B+ sentence pairs |
| **Similarity Function** | Cosine similarity |

**Caching Strategy:**
```python
@lru_cache(maxsize=10000)
def embed_text(self, text: str) -> List[float]:
    """Cached embedding generation."""
    return self.model.encode(text).tolist()
```

**Usage Locations:**
1. RAG retrieval (query embedding)
2. Semantic cache similarity matching
3. Vector store document indexing

### 3.3 Vector Store (ChromaDB)

**Purpose:** Store and retrieve document embeddings for semantic search.

**Implementation:** `rag/vectorstore.py`

**Configuration:**
| Parameter | Value |
|-----------|-------|
| **Persistence Directory** | `data/chroma_db/` |
| **Collection Name** | `onboarding_docs` |
| **Distance Function** | Cosine |
| **Metadata Fields** | department, source, chunk_id |

### 3.4 BM25 Index (Keyword Search)

**Purpose:** Complement semantic search with keyword-based retrieval for exact term matching.

**Implementation:** `rag/hybrid_search.py` - `BM25Index` class

**Algorithm:** BM25Okapi (Best Matching 25 with Okapi weighting)

**Tokenization:**
```python
def _tokenize(self, text: str) -> List[str]:
    text = text.lower()
    tokens = re.findall(r'\b\w+\b', text)
    return tokens
```

### 3.5 Semantic Cache

**Purpose:** Cache LLM responses for similar queries to reduce latency and API costs.

**Implementation:** `app/services/semantic_cache.py`

**Two-Tier Strategy:**

| Tier | Method | Speed | Threshold |
|------|--------|-------|-----------|
| **Tier 1** | Exact hash match (SHA-256) | O(1) ~5ms | Exact match |
| **Tier 2** | Semantic similarity | O(n) ~50ms | Cosine ≥ 0.92 |

**Database Schema:**
```sql
CREATE TABLE semantic_cache (
    id INTEGER PRIMARY KEY,
    query_hash VARCHAR(64) UNIQUE,    -- SHA-256 hash
    query_text TEXT,
    query_embedding JSON,              -- 768-dim vector
    response TEXT,
    sources JSON,
    department VARCHAR(50),
    hit_count INTEGER DEFAULT 0,
    confidence_score FLOAT,
    created_at DATETIME,
    last_accessed DATETIME,
    expires_at DATETIME,               -- TTL: 24 hours
    is_valid BOOLEAN DEFAULT TRUE
);
```

**Cache Operations:**
- `get_cached_response(query)`: Check for cached response
- `cache_response(query, response, ...)`: Store new response
- `invalidate_cache(department)`: Invalidate by department
- `cleanup_expired()`: Remove expired entries

---

## 4. Multi-Agent System

### Overview

The multi-agent system uses **LangGraph** for orchestration, providing a state machine-based approach to route queries through specialized agents. Each agent has domain expertise and access to department-specific knowledge bases.

**Implementation:** `app/agents/orchestrator.py`

### Agent Architecture

| Agent | Class | Department | Knowledge Base | Responsibilities |
|-------|-------|------------|----------------|------------------|
| **Coordinator** | `CoordinatorAgent` | Routing | ML Model | Query classification, department routing, multi-intent detection |
| **HR Agent** | `HRAgent` | HR | `hr_policy.md` | Benefits, PTO, leave, policies, compensation, onboarding |
| **IT Agent** | `ITAgent` | IT | `it_policy.md` | Equipment, VPN, email, accounts, software, tech support |
| **Security Agent** | `SecurityAgent` | Security | `security_policy.md` | Compliance, training, NDAs, access control, data protection |
| **Finance Agent** | `FinanceAgent` | Finance | `finance_policy.md` | Expenses, payroll, travel, reimbursements, budgets |
| **Progress Agent** | `ProgressAgent` | Tasks | User's tasks | Task status, checklist updates, progress tracking |

### Agent State (Shared Context)

```python
class AgentState(TypedDict):
    # User context
    user_id: int
    user_name: str
    user_role: str
    user_department: str
    user_type: str                    # new_hire, employee, admin
    
    # Message context
    current_message: str
    messages: List[Dict[str, str]]    # Chat history
    tasks: List[Dict[str, Any]]       # User's onboarding tasks
    
    # Language context
    language: str                     # "en" or "ar"
    is_arabic: bool
    
    # Routing results
    predicted_department: str
    prediction_confidence: float
    final_department: str
    was_overridden: bool
    
    # Response data
    response: str
    sources: List[Dict[str, Any]]
    task_updates: List[Dict]
    agent_responses: Dict[str, str]   # For multi-intent
    
    # Timing
    start_time: datetime
    end_time: datetime
    total_time_ms: float
```

### LangGraph State Machine

```
┌─────────────────────────────────────────────────────────────────┐
│                    ENTRY POINT                                   │
│                   coordinator                                    │
│    (ML Classification + Keyword Override + Language Detection)  │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
              ▼               ▼               ▼
    ┌─────────────────────────────────────────────────────────────┐
    │                   CONDITIONAL ROUTING                        │
    │   Based on: final_department, multi-intent detection         │
    └─────────────────────────────────────────────────────────────┘
              │
    ┌─────────┼─────────┬─────────┬─────────┬─────────┐
    │         │         │         │         │         │
    ▼         ▼         ▼         ▼         ▼         ▼
┌──────┐ ┌──────┐ ┌────────┐ ┌───────┐ ┌────────┐ ┌────────────┐
│  HR  │ │  IT  │ │Security│ │Finance│ │Progress│ │Multi-Intent│
│Agent │ │Agent │ │ Agent  │ │ Agent │ │ Agent  │ │  Parallel  │
└──────┘ └──────┘ └────────┘ └───────┘ └────────┘ └────────────┘
    │         │         │         │         │         │
    └─────────┴─────────┴─────────┴─────────┴─────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │    finalize     │
                    │ (Response wrap) │
                    └─────────────────┘
                              │
                              ▼
                           [ END ]
```

### Multi-Intent Detection & Handling

**Intent Detector:** `app/services/intent_detector.py`

When a query spans multiple departments (e.g., "What's my PTO balance and how do I set up VPN?"):

1. **Detection Phase:**
   - Intent detector analyzes query for multiple topics
   - Keyword matching identifies relevant departments
   - Returns list of detected departments

2. **Parallel Processing:**
   ```python
   # Run agents in parallel using asyncio.gather
   agent_tasks = [
       self._process_single_agent(dept, base_state.copy())
       for dept in detected_departments
   ]
   responses = await asyncio.gather(*agent_tasks)
   ```

3. **Response Combination:**
   - Responses combined with section headers
   - Duplicate greetings removed from subsequent responses
   - Formatted with department labels

**Example Combined Response:**
```
**HR Information:**
Your current PTO balance is 15 days. To request time off...

---

**IT Information:**
To set up VPN access, follow these steps...
```

### Arabic Query Handling

For Arabic queries, special handling is applied:

1. **Language Detection:** Automatic detection via translation service
2. **Keyword Override:** Arabic keywords bypass ML routing (ML trained on English)
3. **RAG Translation:** Arabic queries translated to English keywords for retrieval
4. **Response Language:** LLM instructed to respond in Arabic

---

## 5. RAG Pipeline

### Overview

The RAG (Retrieval-Augmented Generation) pipeline combines document retrieval with LLM generation to provide accurate, grounded responses based on company policy documents.

**Implementation:** `rag/hybrid_search.py`, `rag/vectorstore.py`, `rag/embeddings.py`

### Hybrid Retrieval Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER QUERY                                │
│            "How do I submit an expense report?"                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
                    ▼                   ▼
┌─────────────────────────────┐ ┌─────────────────────────────┐
│     SEMANTIC SEARCH         │ │      KEYWORD SEARCH         │
│        (ChromaDB)           │ │         (BM25)              │
│                             │ │                             │
│ 1. Embed query (768-dim)    │ │ 1. Tokenize query          │
│ 2. Vector similarity        │ │ 2. TF-IDF scoring          │
│ 3. Return top-K with scores │ │ 3. Return top-K with scores│
│                             │ │                             │
│ Weight: 0.7                 │ │ Weight: 0.3                 │
└─────────────────────────────┘ └─────────────────────────────┘
                    │                   │
                    └─────────┬─────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              RECIPROCAL RANK FUSION (RRF)                        │
│                                                                  │
│  1. Normalize semantic scores to [0, 1]                          │
│  2. Normalize BM25 scores to [0, 1]                              │
│  3. Combined = 0.7 × semantic + 0.3 × BM25                       │
│  4. Deduplicate by document hash                                 │
│  5. Sort by combined score descending                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   TOP-5 DOCUMENT CHUNKS                          │
│                                                                  │
│  Chunk 1: "To submit expenses, use the Finance Portal..."       │
│  Chunk 2: "Expense reports require receipts for..."             │
│  ...                                                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   LLM GENERATION                                 │
│                  (OpenAI GPT-4o-mini)                           │
│                                                                  │
│  System: "You are a helpful onboarding assistant..."            │
│  Context: [Retrieved documents]                                  │
│  User: "How do I submit an expense report?"                      │
│                                                                  │
│  → Generate grounded response with citations                     │
└─────────────────────────────────────────────────────────────────┘
```

### Configuration Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| **Chunk Size** | 500 tokens | Document chunk size for indexing |
| **Chunk Overlap** | 100 tokens | Overlap between adjacent chunks |
| **Top-K Retrieval** | 5 documents | Number of chunks to retrieve |
| **Semantic Weight** | 0.7 | Weight for semantic similarity scores |
| **BM25 Weight** | 0.3 | Weight for keyword matching scores |
| **Fetch Multiplier** | 1.5x | Over-fetch for fusion (7-8 docs initially) |
| **Cache TTL** | 30 minutes | Hybrid search result cache |
| **Cache Size** | 5,000 entries | Maximum cached queries |

### Parallel Search Execution

For performance optimization, semantic and BM25 searches run concurrently:

```python
# Submit both searches to thread pool
semantic_future = _search_executor.submit(
    self._semantic_search, query, fetch_count, department_filter
)
bm25_future = _search_executor.submit(
    self._bm25_search, query, fetch_count, department_filter
)

# Wait for both to complete
semantic_results = semantic_future.result()
bm25_results = bm25_future.result()
```

### Search Response Structure

```python
@dataclass
class HybridSearchResponse:
    results: List[HybridSearchResult]
    query: str
    semantic_time_ms: float
    bm25_time_ms: float
    rerank_time_ms: float
    total_time_ms: float
    cache_hit: bool = False

@dataclass
class HybridSearchResult:
    document: str                 # Chunk text
    metadata: Dict[str, Any]      # department, source, etc.
    semantic_score: float         # Raw semantic score
    bm25_score: float            # Raw BM25 score
    combined_score: float        # Weighted combination
    rank: int                    # Final rank position
```

---

## 6. Query Processing Pipeline

### Complete Request Flow

```
┌──────────────────────────────────────────────────────────────────────┐
│                         USER SUBMITS QUERY                            │
│                "What's the PTO policy and how do I set up VPN?"       │
└──────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────┐
│ STEP 1: LANGUAGE DETECTION                                            │
│ ──────────────────────────────────────────────────────────────────── │
│ translation_service.detect_language(message)                          │
│ Result: "en" (English) or "ar" (Arabic)                               │
└──────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────┐
│ STEP 2: SEMANTIC CACHE CHECK                                          │
│ ──────────────────────────────────────────────────────────────────── │
│ 1. Compute query hash (SHA-256)                                       │
│ 2. Check exact match in semantic_cache table                          │
│ 3. If miss, compute embedding and check semantic similarity           │
│ 4. If hit (similarity ≥ 0.92), return cached response                │
│                                                                       │
│ Cache Hit → Return immediately (~50-100ms)                            │
└──────────────────────────────────────────────────────────────────────┘
                                   │ Cache Miss
                                   ▼
┌──────────────────────────────────────────────────────────────────────┐
│ STEP 3: MULTI-INTENT DETECTION                                        │
│ ──────────────────────────────────────────────────────────────────── │
│ intent_detector.detect(message)                                       │
│ + Keyword scanning for department signals                             │
│                                                                       │
│ Detected: ["HR", "IT"] (multi-intent query)                          │
└──────────────────────────────────────────────────────────────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
           Single Intent                   Multi-Intent
                    │                             │
                    ▼                             ▼
┌──────────────────────────┐   ┌──────────────────────────────────────┐
│ STEP 4A: SINGLE ROUTING   │   │ STEP 4B: PARALLEL MULTI-AGENT        │
│ ───────────────────────── │   │ ────────────────────────────────────│
│ 1. Coordinator classifies │   │ 1. Create agent tasks for each dept │
│ 2. Route to single agent  │   │ 2. Execute in parallel (asyncio)    │
│ 3. Agent retrieves + LLM  │   │ 3. Each agent retrieves + generates │
└──────────────────────────┘   └──────────────────────────────────────┘
                    │                             │
                    ▼                             ▼
┌──────────────────────────────────────────────────────────────────────┐
│ STEP 5: RAG RETRIEVAL (Per Agent)                                     │
│ ──────────────────────────────────────────────────────────────────── │
│ 1. (Arabic) Translate query keywords to English                       │
│ 2. Hybrid search: Semantic + BM25                                     │
│ 3. RRF fusion and ranking                                             │
│ 4. Return top-5 relevant chunks                                       │
└──────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────┐
│ STEP 6: LLM GENERATION                                                │
│ ──────────────────────────────────────────────────────────────────── │
│ Model: OpenAI GPT-4o-mini                                             │
│ System Prompt: Department-specific instructions + language            │
│ Context: Retrieved document chunks                                    │
│ User: Original query                                                  │
│                                                                       │
│ → Generate helpful, grounded response in user's language             │
└──────────────────────────────────────────────────────────────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
           Single Response              Multi-Intent
                    │                             │
                    │                             ▼
                    │              ┌──────────────────────────────────┐
                    │              │ STEP 7: COMBINE RESPONSES         │
                    │              │ ─────────────────────────────────│
                    │              │ 1. Add section headers            │
                    │              │ 2. Remove duplicate greetings     │
                    │              │ 3. Join with separators           │
                    │              └──────────────────────────────────┘
                    │                             │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────┐
│ STEP 8: CACHE RESPONSE (Background Thread)                            │
│ ──────────────────────────────────────────────────────────────────── │
│ ThreadPoolExecutor.submit(cache_in_background)                        │
│ - Store response in semantic_cache table                              │
│ - Non-blocking (doesn't delay response)                               │
└──────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────┐
│ STEP 9: AUDIT LOGGING                                                 │
│ ──────────────────────────────────────────────────────────────────── │
│ AuditLogger.log(AuditAction.CHAT_SEND, ...)                          │
│ Details: query, response, department, confidence, duration_ms        │
└──────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────┐
│ STEP 10: RETURN RESPONSE                                              │
│ ──────────────────────────────────────────────────────────────────── │
│ {                                                                     │
│   "response": "Here's information about PTO...\n\n---\n\nFor VPN...",│
│   "message_id": 123,                                                  │
│   "routing": { "departments": ["HR", "IT"], ... }                     │
│ }                                                                     │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 7. Authentication & Security

### Authentication Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │     │   FastAPI   │     │  Database   │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │
       │  POST /auth/login │                   │
       │  {email, password}│                   │
       │──────────────────>│                   │
       │                   │  Query user       │
       │                   │──────────────────>│
       │                   │  User record      │
       │                   │<──────────────────│
       │                   │                   │
       │                   │ Verify password   │
       │                   │ (bcrypt.verify)   │
       │                   │                   │
       │                   │ Generate tokens   │
       │                   │ (access + refresh)│
       │                   │                   │
       │ {access_token,    │                   │
       │  refresh_token,   │                   │
       │  user}            │                   │
       │<──────────────────│                   │
       │                   │                   │
```

### JWT Token Structure

**Access Token (short-lived: 30 minutes):**
```json
{
  "sub": "123",                          // User ID
  "email": "john.doe@company.com",
  "user_type": "new_hire",               // Role enum
  "session_id": "uuid-session-id",
  "permissions": [                       // Granular permissions
    "chat:send",
    "task:read:own",
    "task:update:own",
    "training:read",
    "calendar:read:own"
  ],
  "exp": 1734567890,                     // Expiration timestamp
  "iat": 1734566090,                     // Issued at
  "type": "access"
}
```

**Refresh Token (long-lived: 7 days):**
```json
{
  "sub": "123",
  "session_id": "uuid-session-id",
  "exp": 1735171890,
  "type": "refresh"
}
```

### Role-Based Access Control (RBAC)

**Implementation:** `app/auth/permissions.py`

| Role | Level | Permissions | Use Case |
|------|-------|-------------|----------|
| **super_admin** | 5 | Full system access, config | System administrators |
| **admin** | 4 | User management, all data, audit | Department heads |
| **hr_admin** | 3 | HR users, policies, FAQs | HR team members |
| **it_admin** | 3 | IT FAQs, system logs | IT support staff |
| **security_admin** | 3 | Security policies, compliance | Security team |
| **manager** | 2 | Team view, reports, churn data | Team managers |
| **employee** | 1 | Own resources, full features | Regular employees |
| **new_hire** | 0 | Basic access, onboarding features | New employees |

**Permission Decorator:**
```python
@router.get("/admin/users")
@require_roles(["admin", "hr_admin"])
async def get_all_users(current_user: User = Depends(get_current_user)):
    # Only accessible by admin or hr_admin roles
    ...
```

### Security Features

| Feature | Implementation | Details |
|---------|---------------|---------|
| **Password Hashing** | bcrypt | Automatic salting, work factor 12 |
| **Account Lockout** | Database flag | 5 failed attempts → 30 min lock |
| **Rate Limiting** | Token bucket | 100 req/min default, configurable |
| **PII Detection** | Regex patterns | SSN, credit cards, emails redacted |
| **Session Management** | DB + JWT | Active session tracking, logout all |
| **CORS** | Middleware | Configurable origins |
| **Input Validation** | Pydantic | Strict type checking |

### Password Hashing

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
```

---

## 8. Audit & Logging System

### Overview

The audit system provides comprehensive tracking of all system activities for compliance, debugging, and security monitoring.

**Implementation:** `app/audit/service.py`, `app/audit/middleware.py`

### Audit Actions

```python
class AuditAction(str, Enum):
    # Authentication
    LOGIN = "auth.login"
    LOGIN_FAILED = "auth.login_failed"
    LOGOUT = "auth.logout"
    TOKEN_REFRESH = "auth.token_refresh"
    REGISTER = "auth.register"
    
    # User management
    USER_CREATE = "user.create"
    USER_UPDATE = "user.update"
    USER_DELETE = "user.delete"
    
    # Task operations
    TASK_CREATE = "task.create"
    TASK_STATUS_CHANGE = "task.status_change"
    
    # Chat operations
    CHAT_SEND = "chat.send"
    CHAT_RECEIVE = "chat.receive"
    
    # Admin operations
    ADMIN_DASHBOARD_VIEW = "admin.dashboard_view"
    ADMIN_AUDIT_VIEW = "admin.audit_view"
    
    # Security events
    SECURITY_PII_DETECTED = "security.pii_detected"
    SECURITY_RATE_LIMIT = "security.rate_limit"
    SECURITY_ACCESS_DENIED = "security.access_denied"
```

### Audit Log Database Schema

```sql
CREATE TABLE audit_logs (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    action VARCHAR(100) NOT NULL,       -- e.g., "chat.send"
    resource_type VARCHAR(50) NOT NULL, -- e.g., "message"
    resource_id INTEGER,
    user_id INTEGER REFERENCES users(id),
    user_email VARCHAR(255),
    session_id VARCHAR(100),
    ip_address VARCHAR(45),             -- IPv4 or IPv6
    user_agent VARCHAR(500),
    details JSON,                        -- Context-specific data
    status VARCHAR(20) DEFAULT 'success', -- success, failure, error
    error_message TEXT,
    
    -- Indexes for efficient querying
    INDEX ix_audit_logs_user_timestamp (user_id, timestamp),
    INDEX ix_audit_logs_action_timestamp (action, timestamp)
);
```

### Chat Audit Details

For `chat.send` actions, the `details` JSON contains comprehensive information:

```json
{
  "query": "What is the PTO policy?",
  "response": "The PTO policy allows employees up to 20 days...",
  "department": "HR",
  "predicted_department": "HR",
  "confidence": 0.87,
  "agent": "hr",
  "duration_ms": 4523.5,
  "is_multi_intent": false,
  "cache_hit": false,
  "sources_count": 3
}
```

### Audit Middleware

The middleware automatically logs all API requests:

```python
class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Capture request details
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Log to audit system
        db = next(get_db())
        audit_logger = AuditLogger(db)
        audit_logger.log(
            action=self._determine_action(request.url.path, request.method),
            resource_type=self._determine_resource(request.url.path),
            user_id=self._extract_user_id(request),
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
            details={"path": request.url.path, "method": request.method},
            status="success" if response.status_code < 400 else "failure"
        )
        
        return response
```

### Audit Explorer UI Features

| Feature | Description |
|---------|-------------|
| **Summary Cards** | Total events, success/failure counts, unique users |
| **Date Range Filter** | Filter logs by custom date range |
| **Action Filter** | Filter by specific action types |
| **User Filter** | Filter by user ID or email |
| **Query/Response Columns** | Display chat content directly in table |
| **Detail Modal** | Full context view for any log entry |
| **CSV Export** | Download filtered logs for external analysis |

---

## 9. Caching Strategy

### Multi-Level Caching Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         REQUEST                                      │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ LEVEL 1: SEMANTIC CACHE (SQLite)                                     │
│ ─────────────────────────────────────────────────────────────────── │
│ Check: SHA-256 hash exact match → Cosine similarity (≥0.92)         │
│ TTL: 24 hours                                                        │
│ Hit: Return cached LLM response (~50-100ms)                         │
└─────────────────────────────────────────────────────────────────────┘
                              │ Miss
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ LEVEL 2: EMBEDDING CACHE (LRU In-Memory)                             │
│ ─────────────────────────────────────────────────────────────────── │
│ Size: 10,000 entries                                                 │
│ Hit: Skip embedding computation (~100ms saved)                       │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ LEVEL 3: HYBRID SEARCH CACHE (TTLCache)                              │
│ ─────────────────────────────────────────────────────────────────── │
│ Size: 5,000 entries | TTL: 30 minutes                               │
│ Key: MD5(query + department + n_results)                             │
│ Hit: Skip RAG retrieval (~200-500ms saved)                          │
└─────────────────────────────────────────────────────────────────────┘
                              │ Miss
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ FULL PIPELINE EXECUTION                                              │
│ Semantic Search + BM25 + RRF + LLM Generation                        │
│ Time: 3-8 seconds                                                    │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ BACKGROUND: CACHE POPULATION                                         │
│ Store response in semantic cache (non-blocking)                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Cache Configuration Summary

| Cache Level | Technology | Size | TTL | Purpose |
|-------------|------------|------|-----|---------|
| **Semantic Cache** | SQLite table | Unlimited | 24 hours | Full LLM responses |
| **Embedding Cache** | `@lru_cache` | 10,000 entries | Session | Query embeddings |
| **Hybrid Search Cache** | `TTLCache` | 5,000 entries | 30 min | Search results |
| **Session Cache** | In-memory dict | Per-user | 60 min | User context |
| **ML Router** | Singleton | 1 model | Permanent | Trained model |

### Performance Impact

| Scenario | Response Time | Cache Hit Rate |
|----------|---------------|----------------|
| **Exact hash match** | ~50ms | ~10-15% |
| **Semantic similarity hit** | ~100ms | ~20-30% |
| **Embedding cache hit** | ~200ms saved | ~80% |
| **Search cache hit** | ~300ms saved | ~40% |
| **Full pipeline (miss)** | 3-8 seconds | N/A |

### Cache Invalidation

```python
# Invalidate by department (e.g., after policy update)
cache_service.invalidate_cache(department="HR")

# Clear expired entries
cache_service.cleanup_expired()

# Clear all search cache
hybrid_search_engine.clear_cache()
```

---

## 10. Database Schema

### Database Overview

**Technology:** SQLite (development) / PostgreSQL (production-ready)  
**ORM:** SQLAlchemy 2.0+ with declarative models  
**Location:** `data/onboarding.db`

### Entity Relationship Diagram

```
┌─────────────┐     ┌─────────────┐     ┌─────────────────┐
│    users    │────<│    tasks    │     │ training_modules│
│             │     │             │     │                 │
│ id (PK)     │     │ id (PK)     │     │ id (PK)         │
│ name        │     │ user_id (FK)│     │ title           │
│ email       │     │ title       │     │ department      │
│ password_hash     │ status      │     │ content (JSON)  │
│ role        │     │ due_date    │     │ passing_score   │
│ department  │     └─────────────┘     └────────┬────────┘
│ user_type   │                                  │
└──────┬──────┘     ┌─────────────┐     ┌────────┴────────┐
       │            │  messages   │     │training_progress│
       │            │             │     │                 │
       ├───────────>│ id (PK)     │     │ id (PK)         │
       │            │ user_id (FK)│<────│ user_id (FK)    │
       │            │ text        │     │ module_id (FK)  │
       │            │ source      │     │ status          │
       │            │ timestamp   │     │ score           │
       │            └──────┬──────┘     └─────────────────┘
       │                   │
       │            ┌──────┴──────┐     ┌─────────────────┐
       │            │  feedback   │     │  achievements   │
       │            │             │     │                 │
       ├───────────>│ id (PK)     │     │ id (PK)         │
       │            │ user_id (FK)│     │ name            │
       │            │ message_id  │     │ category        │
       │            │ feedback_type     │ points          │
       │            │ routing_was_      │ criteria (JSON) │
       │            │   correct   │     └────────┬────────┘
       │            └─────────────┘              │
       │                                ┌────────┴────────┐
       │                                │user_achievements│
       │                                │                 │
       └───────────────────────────────>│ id (PK)         │
                                        │ user_id (FK)    │
                                        │ achievement_id  │
                                        │ progress        │
                                        │ unlocked_at     │
                                        └─────────────────┘
```

### Complete Table Reference

| Table | Description | Key Columns |
|-------|-------------|-------------|
| `users` | User accounts | id, name, email, password_hash, role, department, user_type, preferred_language |
| `tasks` | Onboarding tasks | id, user_id, title, description, status, due_date, department |
| `messages` | Chat history | id, user_id, text, source, language, timestamp, extra_data |
| `feedback` | Response feedback | id, user_id, message_id, feedback_type, routing_was_correct, query_text |
| `achievements` | Achievement definitions | id, name, description, icon, category, points, criteria |
| `user_achievements` | Unlocked achievements | id, user_id, achievement_id, progress, unlocked_at |
| `training_modules` | Training content | id, title, department, content, passing_score, is_required |
| `training_progress` | User training progress | id, user_id, module_id, status, score, attempts |
| `calendar_events` | Calendar entries | id, user_id, title, start_time, end_time, task_id |
| `faqs` | FAQ entries | id, question, answer, category, department, tags |
| `workflows` | Automation rules | id, name, trigger, conditions, actions, is_active |
| `workflow_executions` | Workflow run logs | id, workflow_id, user_id, status, result |
| `engagement_metrics` | Daily engagement | id, user_id, date, chat_messages_sent, tasks_completed |
| `churn_predictions` | Churn risk data | id, user_id, risk_level, churn_probability, risk_factors |
| `audit_logs` | Audit trail | id, timestamp, action, user_id, details, status |
| `routing_logs` | ML routing logs | id, query_text, predicted_department, confidence |
| `semantic_cache` | Query cache | id, query_hash, query_text, response, expires_at |
| `user_sessions` | Session management | id, session_id, user_id, refresh_token_hash, expires_at |

### Key Enumerations

```python
class TaskStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"

class Department(str, Enum):
    HR = "HR"
    IT = "IT"
    SECURITY = "Security"
    FINANCE = "Finance"
    GENERAL = "General"

class UserRole(str, Enum):
    NEW_HIRE = "new_hire"
    EMPLOYEE = "employee"
    MANAGER = "manager"
    HR_ADMIN = "hr_admin"
    IT_ADMIN = "it_admin"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"

class ChurnRisk(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AchievementCategory(str, Enum):
    ONBOARDING = "onboarding"
    LEARNING = "learning"
    ENGAGEMENT = "engagement"
    SPEED = "speed"
    SOCIAL = "social"
```

---

## 11. Gamification & Achievements

### Overview

The gamification system encourages engagement through achievements, points, and leaderboards.

**Implementation:** `app/services/achievements.py`

### Achievement Categories

| Category | Description | Examples |
|----------|-------------|----------|
| **Onboarding** | Task completion milestones | First Steps, Getting Started, Onboarding Pro |
| **Learning** | Training module progress | Training Champion, Perfect Score |
| **Engagement** | Chat and platform interaction | Curious Mind, Knowledge Seeker, Feedback Helper |
| **Speed** | Quick task completion | Quick Learner, Early Bird |
| **Social** | Collaboration metrics | (Future: Team Player, Mentor) |

### Achievement Definitions (12 Total)

| Achievement | Icon | Points | Criteria |
|-------------|------|--------|----------|
| First Steps | 🎯 | 10 | Complete 1 onboarding task |
| Getting Started | ⭐ | 25 | Complete 5 onboarding tasks |
| Onboarding Pro | 🏆 | 100 | Complete all onboarding tasks |
| Quick Learner | ⚡ | 50 | Complete onboarding within 7 days |
| Curious Mind | ❓ | 15 | Ask 10 questions |
| Knowledge Seeker | 📚 | 40 | Ask 50 questions |
| Training Champion | 🎓 | 75 | Complete all training modules |
| Perfect Score | 💯 | 30 | Score 100% on a quiz |
| Feedback Helper | 👍 | 20 | Provide feedback on 5 responses |
| Early Bird | 🌅 | 15 | Complete a task before due date |
| Streak Starter | 🔥 | 20 | Log in 3 days in a row |
| Dedicated | 💪 | 50 | Log in 7 days in a row |

### Achievement Criteria Types

```python
# Tasks completed count
{"type": "tasks_completed", "count": 5}

# All tasks completed
{"type": "all_tasks_completed"}

# Questions asked count
{"type": "questions_asked", "count": 10}

# Onboarding speed (days)
{"type": "onboarding_speed", "days": 7}

# All training completed
{"type": "all_training_completed"}

# Perfect quiz score
{"type": "quiz_perfect_score"}

# Early task completion
{"type": "early_completion"}

# Feedback given count
{"type": "feedback_given", "count": 5}
```

### Automatic Achievement Checking

Achievements are checked automatically after relevant actions:

```python
# In routes.py after task status change
achievement_service = AchievementService(db)
newly_unlocked = achievement_service.check_and_unlock(current_user.id)

# In routes.py after chat message
newly_unlocked = achievement_service.check_and_unlock(current_user.id)
```

---

## 12. Churn Prediction System

### Overview

The churn prediction system identifies at-risk employees based on engagement patterns.

**Implementation:** `app/services/churn_prediction.py`

### Engagement Score Calculation

```python
WEIGHTS = {
    "task_completion": 0.30,      # 30% - Task completion rate
    "activity_frequency": 0.25,   # 25% - Login/activity frequency
    "learning_progress": 0.20,    # 20% - Training module completion
    "chat_engagement": 0.15,      # 15% - Chat interactions
    "feedback_sentiment": 0.10    # 10% - Positive/negative feedback ratio
}
```

### Score Components

| Component | Calculation | Max Score |
|-----------|-------------|-----------|
| **Task Score** | (completed/total) + (in_progress * 0.3) - (overdue * 0.5) | 100 |
| **Activity Score** | (active_days / expected_days) * 100 | 100 |
| **Learning Score** | (completed_modules * 60) + (in_progress * 20) + (avg_score * 20) | 100 |
| **Interaction Score** | (messages * 0.6) + (sentiment * 0.4) | 100 |

### Risk Level Thresholds

| Risk Level | Score Range | Color | Action Required |
|------------|-------------|-------|-----------------|
| **LOW** | 65-100 | Green | Continue monitoring |
| **MEDIUM** | 45-65 | Yellow | Send engagement reminders |
| **HIGH** | 25-45 | Orange | Schedule 1-on-1 check-in |
| **CRITICAL** | 0-25 | Red | Immediate intervention, escalate to HR |

### Risk Factors Detection

The system identifies specific risk factors:

- Low task completion rate (<40%)
- Infrequent platform activity (<30%)
- Training modules incomplete (<50%)
- Low engagement with assistant (<40%)
- Overdue tasks present
- No activity in X days
- Onboarding behind schedule (>30 days, <50% complete)

### Recommended Actions

Based on risk factors, the system generates action recommendations:

| Risk Factor | Recommended Actions |
|-------------|---------------------|
| Low task completion | Review and prioritize tasks, extend deadlines |
| Infrequent activity | Send engagement reminder, highlight quick wins |
| Training incomplete | Send training reminder, offer assistance |
| Overdue tasks | Address overdue tasks immediately |
| No recent activity | Reach out via email/phone |
| HIGH/CRITICAL risk | Schedule 1-on-1, assign buddy/mentor |
| CRITICAL risk | Escalate to HR for intervention |

---

## 13. Feedback System

### Overview

The feedback system collects user opinions on AI responses to improve quality and enable model retraining.

**Implementation:** `app/services/feedback.py`

### Feedback Types

```python
class FeedbackType(str, Enum):
    HELPFUL = "helpful"         # Thumbs up
    NOT_HELPFUL = "not_helpful" # Thumbs down
```

### Feedback Data Model

```python
class Feedback(Base):
    id: int                       # Primary key
    user_id: int                  # User who gave feedback
    message_id: int               # Message being rated
    feedback_type: FeedbackType   # helpful/not_helpful
    comment: Optional[str]        # Free-text comment
    routing_was_correct: bool     # Was department routing correct?
    answer_was_accurate: bool     # Was the answer accurate?
    query_text: str               # Original query (for retraining)
    predicted_department: str     # ML-predicted department
    suggested_department: str     # User-suggested correct department
    created_at: datetime
```

### Feedback Integration with AI

1. **Quality Monitoring:**
   - Feedback stats tracked (helpful_rate, routing_accuracy)
   - Negative feedback flagged for review

2. **Model Retraining Data:**
   ```python
   def get_feedback_for_retraining(self, limit: int = 1000):
       """Extract labeled data for model improvement."""
       # Returns query + correct department for retraining
   ```

3. **Churn Prediction Integration:**
   - Positive feedback → increases engagement score
   - Negative feedback → decreases engagement score
   - Sentiment ratio affects churn risk

### Feedback Flow

```
User receives response → Clicks 👍 or 👎 → 
  → (Optional) Provides comment →
  → Feedback saved with routing info →
  → Used for: Analytics, Retraining, Churn Prediction
```

---

## 14. Internationalization (i18n)

### Overview

The system supports English and Arabic with full RTL (right-to-left) layout support.

**Implementation:** `app/services/i18n.py`, `ui/src/lib/i18n-context.tsx`

### Supported Languages

| Language | Code | Direction | Status |
|----------|------|-----------|--------|
| English | `en` | LTR | Full support |
| Arabic | `ar` | RTL | Full support |

### Translation Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      FRONTEND                                    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                 I18nProvider (Context)                    │   │
│  │  - currentLanguage: "en" | "ar"                          │   │
│  │  - translations: Record<string, string>                   │   │
│  │  - t(key): string                                        │   │
│  │  - setLanguage(lang): void                               │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Component uses t("key")                      │   │
│  │              e.g., t("calendar.title")                    │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼ API Call
┌─────────────────────────────────────────────────────────────────┐
│                      BACKEND                                     │
│  GET /api/v1/i18n/{lang}                                        │
│  Returns: { "calendar.title": "Calendar", ... }                  │
└─────────────────────────────────────────────────────────────────┘
```

### Database Multilingual Support

All user-facing content has Arabic translations:

```python
# Task model
title = Column(String(255))
title_ar = Column(String(255))  # Arabic translation
description = Column(Text)
description_ar = Column(Text)   # Arabic translation

# Achievement model
name = Column(String(100))
name_ar = Column(String(100))   # Arabic translation
description = Column(Text)
description_ar = Column(Text)   # Arabic translation
```

### Arabic Query Handling in RAG

For Arabic queries, special processing is applied:

1. **Language Detection:**
   ```python
   detected_language = translation_service.detect_language(message)
   is_arabic = detected_language.value == "ar"
   ```

2. **Keyword Translation for Retrieval:**
   Arabic queries are translated to English keywords for RAG:
   ```python
   arabic_to_english = {
       "تأمين صحي": "health insurance",
       "إجازة": "vacation leave PTO",
       "راتب": "salary payroll",
       ...
   }
   ```

3. **Response in User's Language:**
   The LLM is instructed to respond in the detected language.

---

## 15. API Reference

### API Documentation

**Interactive Docs:** `http://localhost:8000/docs` (Swagger UI)  
**OpenAPI Spec:** `http://localhost:8000/openapi.json`

### Authentication Endpoints

| Endpoint | Method | Auth | Request Body | Response |
|----------|--------|------|--------------|----------|
| `/api/v1/auth/login` | POST | No | `{email, password}` | `{access_token, refresh_token, user}` |
| `/api/v1/auth/register` | POST | No | `{name, email, password, role, department}` | `{user}` |
| `/api/v1/auth/refresh` | POST | Refresh | `{refresh_token}` | `{access_token}` |
| `/api/v1/auth/logout` | POST | Yes | - | `{message}` |
| `/api/v1/auth/me` | GET | Yes | - | `{user}` |

### Chat Endpoints

| Endpoint | Method | Auth | Request Body | Response |
|----------|--------|------|--------------|----------|
| `/api/v1/chat` | POST | Yes | `{message, language?}` | `{response, message_id, routing}` |
| `/api/v1/chat/history` | GET | Yes | - | `[{messages}]` |

**Chat Response Structure:**
```json
{
  "response": "Here's information about...",
  "message_id": 123,
  "routing": {
    "predicted_department": "HR",
    "prediction_confidence": 0.87,
    "final_department": "HR",
    "was_overridden": false,
    "is_multi_intent": false,
    "is_cached": false
  }
}
```

### Task Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/v1/tasks` | GET | Yes | Get user's tasks |
| `/api/v1/tasks/{id}` | GET | Yes | Get single task |
| `/api/v1/tasks/{id}/status` | POST | Yes | Update task status |
| `/api/v1/tasks` | POST | Admin | Create new task |

### Training Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/v1/training/modules` | GET | Yes | List training modules |
| `/api/v1/training/modules/{id}` | GET | Yes | Get module content |
| `/api/v1/training/progress` | GET | Yes | User's training progress |
| `/api/v1/training/modules/{id}/submit` | POST | Yes | Submit quiz answers |

### Achievement Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/v1/achievements` | GET | Yes | User achievements (all) |
| `/api/v1/achievements/unlocked` | GET | Yes | Unlocked achievements only |
| `/api/v1/achievements/leaderboard` | GET | Yes | Points leaderboard |
| `/api/v1/achievements/points` | GET | Yes | User's total points |
| `/api/v1/achievements/notifications` | GET | Yes | Unnotified achievements |

### Calendar Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/v1/calendar/events` | GET | Yes | User's calendar events |
| `/api/v1/calendar/events` | POST | Yes | Create calendar event |
| `/api/v1/calendar/events/{id}` | PUT | Yes | Update event |
| `/api/v1/calendar/events/{id}` | DELETE | Yes | Delete event |
| `/api/v1/calendar/export` | GET | Yes | Export as ICS |

### Feedback Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/v1/feedback` | POST | Yes | Submit feedback |
| `/api/v1/feedback/stats` | GET | Admin | Feedback statistics |

### FAQ Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/v1/faqs` | GET | Yes | List FAQs (with search) |
| `/api/v1/faqs/{id}` | GET | Yes | Get single FAQ |
| `/api/v1/faqs` | POST | Admin | Create FAQ |
| `/api/v1/faqs/{id}` | PUT | Admin | Update FAQ |
| `/api/v1/faqs/{id}` | DELETE | Admin | Delete FAQ |
| `/api/v1/faqs/categories` | GET | Yes | List categories |

### Admin Endpoints

| Endpoint | Method | Role Required | Description |
|----------|--------|---------------|-------------|
| `/api/v1/admin/users` | GET | admin, hr_admin | List all users |
| `/api/v1/admin/users` | POST | admin, hr_admin | Create user |
| `/api/v1/admin/users/{id}` | GET | admin, hr_admin | Get user details |
| `/api/v1/admin/metrics` | GET | admin, manager | Dashboard metrics |
| `/api/v1/admin/dashboard` | GET | admin, manager | Dashboard data |

### Audit Endpoints

| Endpoint | Method | Role Required | Description |
|----------|--------|---------------|-------------|
| `/api/v1/audit/logs` | GET | admin | List audit logs (paginated) |
| `/api/v1/audit/logs/search` | POST | admin | Search audit logs |
| `/api/v1/audit/summary` | GET | admin | Audit summary stats |

### Churn Prediction Endpoints

| Endpoint | Method | Role Required | Description |
|----------|--------|---------------|-------------|
| `/api/v1/churn/risk/{user_id}` | GET | admin, manager | User's churn risk |
| `/api/v1/churn/at-risk` | GET | admin, manager | All at-risk users |
| `/api/v1/churn/predict/{user_id}` | POST | admin | Generate prediction |

### i18n Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/v1/i18n/{lang}` | GET | No | Get translations for language |
| `/api/v1/i18n/languages` | GET | No | List available languages |

---

## 16. Frontend Architecture

### Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Framework** | Next.js 14 | React framework with App Router |
| **UI Library** | React 18 | Component library |
| **Styling** | TailwindCSS 3.4 | Utility-first CSS |
| **Animation** | Framer Motion 10 | UI animations |
| **Icons** | Lucide React | Icon library |
| **State** | React Context | Global state management |
| **HTTP Client** | Fetch API | API communication |

### Project Structure

```
ui/src/
├── app/
│   ├── layout.tsx          # Root layout with HTML structure
│   ├── page.tsx            # Main page with view routing
│   ├── providers.tsx       # Context providers (Auth, I18n)
│   └── globals.css         # Global styles
│
├── components/
│   ├── ChatInterface.tsx   # AI chat interface
│   │   ├── Message bubbles (user/assistant)
│   │   ├── FAQ quick actions
│   │   ├── Typing indicator
│   │   └── FeedbackButtons integration
│   │
│   ├── TaskList.tsx        # Onboarding task management
│   │   ├── Task cards with status
│   │   ├── Progress bar
│   │   ├── Overdue detection
│   │   └── Status toggle
│   │
│   ├── AchievementsPanel.tsx # Gamification display
│   │   ├── All/Unlocked tabs
│   │   ├── Achievement cards
│   │   ├── Points display
│   │   └── Leaderboard
│   │
│   ├── TrainingModules.tsx # Learning system
│   │   ├── Module cards
│   │   ├── Progress tracking
│   │   └── Quiz interface
│   │
│   ├── CalendarView.tsx    # Calendar management
│   │   ├── Month view grid
│   │   ├── Event display
│   │   ├── Add event modal
│   │   └── ICS export
│   │
│   ├── FAQManagement.tsx   # FAQ CRUD (admin)
│   ├── ChurnDashboard.tsx  # At-risk users (admin)
│   ├── AuditLogExplorer.tsx # Audit logs (admin)
│   ├── AdminDashboard.tsx  # Metrics dashboard
│   ├── FeedbackButtons.tsx # 👍👎 feedback
│   ├── LoginForm.tsx       # Authentication
│   ├── RegisterForm.tsx    # User registration
│   └── LanguageSwitcher.tsx # EN/AR toggle
│
└── lib/
    ├── api.ts              # API client class
    ├── auth-context.tsx    # Authentication context
    └── i18n-context.tsx    # Internationalization context
```

### State Management

**Authentication Context:**
```typescript
interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}
```

**I18n Context:**
```typescript
interface I18nContextType {
  language: 'en' | 'ar';
  translations: Record<string, string>;
  t: (key: string) => string;
  setLanguage: (lang: 'en' | 'ar') => void;
}
```

**Chat Messages State (Lifted):**
```typescript
// In page.tsx - persists across tab changes
const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);

// Passed to ChatInterface
<ChatInterface 
  messages={chatMessages} 
  setMessages={setChatMessages} 
/>
```

### Key UI Features

| Feature | Implementation |
|---------|----------------|
| **Fixed Chat Container** | `max-h-[calc(100vh-8rem)]` with internal scroll |
| **High Contrast Text** | `text-gray-900` / `text-gray-700` for readability |
| **RTL Support** | `dir="rtl"` when Arabic selected |
| **Responsive Design** | TailwindCSS breakpoints (sm, md, lg) |
| **Loading States** | Framer Motion animations |
| **Error Handling** | Toast notifications |

---

## 17. Performance Optimizations

### Backend Optimizations

| Optimization | Implementation | Impact | Location |
|--------------|----------------|--------|----------|
| **Parallel DB Queries** | `asyncio.gather` for user/tasks | -40% latency | `routes.py` |
| **Background Tasks** | `ThreadPoolExecutor` for saves | Non-blocking | `routes.py`, `orchestrator.py` |
| **Embedding Cache** | `@lru_cache(maxsize=10000)` | -80% embedding time | `embeddings.py` |
| **Parallel Search** | Concurrent semantic + BM25 | -30% search time | `hybrid_search.py` |
| **Preloading** | Startup model initialization | Faster first request | `main.py` |
| **Response Caching** | Background cache writes | Non-blocking | `orchestrator.py` |
| **Query Deduplication** | Hash-based exact match | O(1) lookup | `semantic_cache.py` |

### Parallel Execution Examples

**Chat Endpoint - Parallel Data Fetching:**
```python
# Fetch user data and tasks in parallel
user_data, tasks_data = await asyncio.gather(
    get_user_details(user_id),
    get_user_tasks(user_id)
)
```

**Hybrid Search - Parallel Retrieval:**
```python
# Run semantic and BM25 search concurrently
semantic_future = executor.submit(semantic_search, query)
bm25_future = executor.submit(bm25_search, query)

semantic_results = semantic_future.result()
bm25_results = bm25_future.result()
```

**Background Caching:**
```python
def _cache_response(self, query, response, ...):
    """Cache response without blocking response."""
    def cache_in_background():
        db = next(get_db())
        cache_service = SemanticCacheService(db)
        cache_service.cache_response(query, response, ...)
        db.close()
    
    executor = ThreadPoolExecutor(max_workers=1)
    executor.submit(cache_in_background)
    executor.shutdown(wait=False)  # Don't wait
```

### Startup Preloading

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Preload ML models and services on startup
    logger.info("Preloading ML router...")
    from ml.router import get_router
    _ = get_router()  # Load model into memory
    
    logger.info("Preloading orchestrator...")
    from app.agents.orchestrator import get_orchestrator
    _ = get_orchestrator()  # Initialize agents
    
    logger.info("Preloading embedding model...")
    from rag.embeddings import get_embedding_service
    _ = get_embedding_service()  # Load SentenceTransformer
    
    yield  # Application runs
    
    logger.info("Shutting down...")
```

### Frontend Optimizations

| Optimization | Implementation | Benefit |
|--------------|----------------|---------|
| **State Lifting** | Chat messages in parent component | Persist across tab switches |
| **Conditional Rendering** | Only render visible components | Reduced DOM nodes |
| **Optional Chaining** | `user?.name ?? 'User'` | Prevent crashes on undefined |
| **Fixed Containers** | `overflow-y-auto` with max-height | Smooth scrolling |

### Response Time Breakdown

| Phase | Uncached | Cached |
|-------|----------|--------|
| **JWT Validation** | ~5ms | ~5ms |
| **Cache Check** | ~10ms | ~10ms |
| **Semantic Cache Hit** | - | ~50ms (return) |
| **Language Detection** | ~20ms | - |
| **Intent Detection** | ~50ms | - |
| **ML Routing** | ~30ms | - |
| **RAG Retrieval** | ~500ms | - |
| **LLM Generation** | ~2-5s | - |
| **Response Caching** | ~0ms (background) | - |
| **Audit Logging** | ~0ms (background) | - |
| **Total** | **3-8 seconds** | **~50-100ms** |

---

## 18. Deployment Guide

### Local Development Setup

**Prerequisites:**
- Python 3.11+
- Node.js 18+
- npm 9+

**Step-by-Step:**

```bash
# 1. Clone and navigate
git clone <repository>
cd onboardingAI_agents

# 2. Create Python virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Set environment variables
export OPENAI_API_KEY="your-api-key"
export SECRET_KEY="your-secret-key-min-32-chars"

# 5. Initialize the system (database, sample data, train model)
python scripts/init_system.py

# 6. Start the backend
python -m app.main
# Backend runs at http://localhost:8000

# 7. In a new terminal, start the frontend
cd ui
npm install
npm run dev
# Frontend runs at http://localhost:3000

# 8. (Optional) Start MLflow for model tracking
mlflow ui --port 5001
# MLflow runs at http://localhost:5001
```

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | **Yes** | - | OpenAI API key for LLM |
| `SECRET_KEY` | **Yes** | - | JWT signing key (min 32 chars) |
| `DATABASE_URL` | No | `sqlite:///./data/onboarding.db` | Database connection string |
| `DEBUG` | No | `true` | Enable debug mode |
| `LOG_LEVEL` | No | `INFO` | Logging level |
| `MLFLOW_TRACKING_URI` | No | `mlruns` | MLflow tracking directory |
| `CORS_ORIGINS` | No | `http://localhost:3000` | Allowed CORS origins |

### Demo Accounts

| Role | Email | Password |
|------|-------|----------|
| **Admin** | admin@company.com | admin123 |
| **Manager** | manager@company.com | manager123 |
| **New Hire** | john.doe@company.com | password123 |

### Docker Deployment

```bash
# Build and run all services
docker-compose up --build

# Run in detached mode
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

**docker-compose.yml structure:**
```yaml
services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY
      - SECRET_KEY
    volumes:
      - ./data:/app/data
  
  frontend:
    build: ./ui
    ports:
      - "3000:3000"
    depends_on:
      - backend
  
  mlflow:
    image: python:3.11
    command: mlflow ui --host 0.0.0.0 --port 5001
    ports:
      - "5001:5001"
    volumes:
      - ./mlruns:/mlruns
```

### Production Considerations

| Concern | Recommendation |
|---------|----------------|
| **Database** | Migrate to PostgreSQL for concurrent access |
| **Secrets** | Use environment variables or secrets manager |
| **HTTPS** | Use reverse proxy (nginx) with SSL certificates |
| **Scaling** | Use Gunicorn with multiple workers |
| **Monitoring** | Integrate Prometheus + Grafana |
| **Logging** | Centralize logs with ELK stack |

---

## 19. Testing & Validation

### Health Check Script

```bash
python scripts/health_check.py
```

**Validates:**
- ✅ Backend server responding (GET /health)
- ✅ Database connectivity (SQLite/PostgreSQL)
- ✅ ML routing model loaded
- ✅ Embedding model loaded
- ✅ Vector store accessible
- ✅ Authentication flow working
- ✅ All API endpoints responding

### RAG Evaluation

```bash
python scripts/evaluate_rag.py
```

**Metrics:**
| Metric | Description | Target |
|--------|-------------|--------|
| **Hit Rate** | Document found in top-K | >90% |
| **MRR** | Mean Reciprocal Rank | >0.7 |
| **Retrieval Latency** | Time to retrieve | <500ms |
| **Answer Relevance** | Human evaluation | >4/5 |

### Manual Testing Checklist

**Authentication:**
- [ ] Login with valid credentials
- [ ] Login with invalid credentials (should fail)
- [ ] Token refresh
- [ ] Logout and session invalidation
- [ ] Account lockout after 5 failed attempts

**Chat:**
- [ ] Send English query
- [ ] Send Arabic query (RTL response)
- [ ] Multi-intent query (HR + IT)
- [ ] Cache hit (repeat query)
- [ ] Feedback submission

**Tasks:**
- [ ] View all tasks
- [ ] Update task status (NOT_STARTED → IN_PROGRESS → DONE)
- [ ] Overdue task detection

**Achievements:**
- [ ] View all achievements
- [ ] Achievement unlocks after completing task
- [ ] Points calculation
- [ ] Leaderboard display

**Admin:**
- [ ] View dashboard metrics
- [ ] View audit logs
- [ ] View at-risk users (churn)
- [ ] FAQ management (CRUD)

### API Testing with curl

```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@company.com", "password": "admin123"}'

# Chat (with token)
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the PTO policy?"}'

# Get tasks
curl http://localhost:8000/api/v1/tasks \
  -H "Authorization: Bearer <token>"
```

---

## 20. Known Issues & Limitations

### Current Limitations

| Category | Limitation | Impact | Workaround/Mitigation |
|----------|------------|--------|----------------------|
| **Database** | SQLite single-file | Medium | Migrate to PostgreSQL for production concurrency |
| **Email** | No real email sending | Low | Integrate SMTP/SendGrid for notifications |
| **Notifications** | No push notifications | Low | Add WebSocket support |
| **Calendar** | External OAuth disabled | Low | Configure Google/Outlook credentials |
| **ML Model** | English-only training | Medium | Expand training data for Arabic |
| **Churn** | Rule-based prediction | Medium | Implement ML-based model with more features |
| **Search** | No typo correction | Low | Add fuzzy matching or spell check |
| **Sessions** | JWT-only auth | Low | Add refresh token rotation |

### Known Edge Cases

| Issue | Description | Status |
|-------|-------------|--------|
| **Long queries** | Queries >1000 chars may truncate | Monitoring |
| **Concurrent writes** | SQLite lock on high traffic | Use PostgreSQL |
| **Cache invalidation** | Manual invalidation required after policy updates | Documented |
| **Arabic embedding** | Lower quality for mixed Arabic/English | Use translation layer |

---

## 21. Future Roadmap

### Short-Term (1-3 months)

| Feature | Priority | Status | Notes |
|---------|----------|--------|-------|
| PostgreSQL migration | High | Planned | Connection pooling support |
| Real email integration | High | Planned | SendGrid/SES integration |
| External calendar OAuth | Medium | ✅ Code Ready | Uncomment and configure |
| Two-factor authentication | Medium | Planned | TOTP support |
| Webhook notifications | Medium | Planned | For external integrations |

### Medium-Term (3-6 months)

| Feature | Priority | Notes |
|---------|----------|-------|
| Mobile app (React Native) | High | Cross-platform iOS/Android |
| Slack/Teams integration | High | Bot commands for common actions |
| Advanced analytics | Medium | Engagement dashboards, trends |
| Custom workflow builder | Medium | Visual workflow editor |
| ML-based churn prediction | Medium | Replace rule-based system |

### Long-Term (6-12 months)

| Feature | Priority | Notes |
|---------|----------|-------|
| Multi-tenant architecture | High | SaaS deployment |
| Custom LLM fine-tuning | Medium | Company-specific model |
| Video onboarding modules | Medium | Interactive video content |
| Integration marketplace | Low | Third-party app ecosystem |
| Voice interface | Low | Speech-to-text integration |

---

## 22. Appendices

### Appendix A: File Structure Overview

```
onboardingAI_agents/
├── app/                          # Backend application
│   ├── agents/                   # Multi-agent system
│   │   ├── base.py              # Base agent class
│   │   ├── coordinator.py       # Routing agent
│   │   ├── hr_agent.py          # HR specialist
│   │   ├── it_agent.py          # IT specialist
│   │   ├── security_agent.py    # Security specialist
│   │   ├── finance_agent.py     # Finance specialist
│   │   ├── progress_agent.py    # Task progress agent
│   │   └── orchestrator.py      # LangGraph orchestrator
│   ├── api/                      # API routes
│   │   ├── routes.py            # Main routes
│   │   ├── feature_routes.py    # Feature-specific routes
│   │   └── schemas.py           # Pydantic models
│   ├── audit/                    # Audit system
│   │   ├── service.py           # Audit logger
│   │   └── middleware.py        # Audit middleware
│   ├── auth/                     # Authentication
│   │   ├── jwt.py               # JWT handling
│   │   └── permissions.py       # RBAC
│   ├── database/                 # Database layer
│   │   ├── models.py            # SQLAlchemy models
│   │   └── connection.py        # DB connection
│   ├── services/                 # Business logic
│   │   ├── achievements.py      # Gamification
│   │   ├── churn_prediction.py  # Churn analysis
│   │   ├── feedback.py          # Feedback collection
│   │   ├── i18n.py              # Internationalization
│   │   └── semantic_cache.py    # Query caching
│   ├── config.py                 # Configuration
│   └── main.py                   # FastAPI entry point
│
├── ml/                           # Machine learning
│   ├── router.py                # Question router
│   └── training.py              # Model training
│
├── rag/                          # RAG pipeline
│   ├── embeddings.py            # Embedding service
│   ├── vectorstore.py           # ChromaDB wrapper
│   └── hybrid_search.py         # Hybrid retrieval
│
├── data/                         # Data storage
│   ├── onboarding.db            # SQLite database
│   ├── chroma_db/               # Vector store
│   ├── policies/                # Policy documents
│   └── routing_dataset.json     # Training data
│
├── ui/                           # Frontend
│   ├── src/app/                 # Next.js app
│   ├── src/components/          # React components
│   └── src/lib/                 # Utilities
│
├── scripts/                      # Utility scripts
│   ├── init_system.py           # System initialization
│   ├── health_check.py          # Health validation
│   └── evaluate_rag.py          # RAG evaluation
│
├── docs/                         # Documentation
│   ├── SYSTEM_ARCHITECTURES.md  # Architecture details
│   ├── FEATURES_AND_LIMITATIONS.md
│   └── TECHNICAL_REPORT.md      # This document
│
├── models/                       # Trained models
│   └── question_router.joblib   # Routing model
│
├── mlruns/                       # MLflow experiments
├── requirements.txt              # Python dependencies
└── README.md                     # Quick start guide
```

### Appendix B: Configuration Reference

See `app/config.py` for all configuration options:

```python
class Settings(BaseSettings):
    # API
    app_name: str = "Onboarding Copilot"
    debug: bool = True
    
    # Authentication
    secret_key: str
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    
    # Database
    database_url: str = "sqlite:///./data/onboarding.db"
    
    # AI/ML
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"
    embedding_model: str = "all-mpnet-base-v2"
    
    # Directories
    data_dir: Path = Path("data")
    models_dir: Path = Path("models")
    policies_dir: Path = Path("data/policies")
```

### Appendix C: Related Documentation

| Document | Path | Description |
|----------|------|-------------|
| **README** | `README.md` | Quick start guide |
| **System Architectures** | `docs/SYSTEM_ARCHITECTURES.md` | Detailed architecture diagrams |
| **Features & Limitations** | `docs/FEATURES_AND_LIMITATIONS.md` | Feature catalog |
| **API Documentation** | `http://localhost:8000/docs` | Interactive Swagger UI |

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | Dec 2025 | Initial comprehensive documentation |
| 0.0.2 | Dec 2025 | Draft version with basic structure |

---

## References

- **LangGraph Documentation:** https://langchain-ai.github.io/langgraph/
- **FastAPI Documentation:** https://fastapi.tiangolo.com/
- **ChromaDB Documentation:** https://docs.trychroma.com/
- **Sentence Transformers:** https://www.sbert.net/
- **MLflow Documentation:** https://mlflow.org/docs/latest/index.html

---

*This document provides a comprehensive technical overview of the Enterprise Onboarding Copilot system. For specific implementation details, refer to the source code and inline documentation.*

**Last Updated:** December 2025  
**Document Version:** 1.0.0

