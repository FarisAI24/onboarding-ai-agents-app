# Enterprise Onboarding Copilot - Visual Diagrams

This file contains Mermaid diagrams for the Enterprise Onboarding Copilot system. These diagrams can be viewed:

1. **GitHub/GitLab**: Renders automatically when viewing markdown files
2. **VS Code**: Install "Markdown Preview Mermaid Support" extension, then press `Cmd+Shift+V`
3. **Online**: Paste into [mermaid.live](https://mermaid.live) to view and export

---

## Table of Contents

1. [High-Level System Architecture](#1-high-level-system-architecture)
2. [Data Flow Architecture](#2-data-flow-architecture)
3. [LangGraph Multi-Agent State Machine](#3-langgraph-multi-agent-state-machine)
4. [RAG Hybrid Retrieval Pipeline](#4-rag-hybrid-retrieval-pipeline)
5. [Query Processing Pipeline](#5-query-processing-pipeline)
6. [Authentication Flow](#6-authentication-flow)
7. [Multi-Level Caching Architecture](#7-multi-level-caching-architecture)
8. [Entity Relationship Diagram](#8-entity-relationship-diagram)
9. [Internationalization Architecture](#9-internationalization-architecture)
10. [Request Lifecycle](#10-request-lifecycle)

---

## 1. High-Level System Architecture

```mermaid
flowchart TB
    subgraph Presentation["PRESENTATION LAYER<br/>Next.js 14 + React 18 + TailwindCSS"]
        Chat[Chat Interface]
        Tasks[Tasks List]
        Training[Training Modules]
        Calendar[Calendar View]
        Achievements[Achievements]
        Admin[Admin Dashboard]
    end

    subgraph API["API LAYER<br/>FastAPI + Middleware Stack"]
        subgraph Middleware[Middleware]
            CORS[CORS]
            RateLimit[Rate Limit]
            JWTAuth[JWT Auth]
            RBAC[RBAC]
            PII[PII Redact]
            Audit[Audit Logging]
        end
        subgraph Endpoints[API Endpoints]
            AuthAPI[/auth]
            ChatAPI[/chat]
            TasksAPI[/tasks]
            TrainingAPI[/training]
            AdminAPI[/admin]
            AuditAPI[/audit]
        end
    end

    subgraph Service["SERVICE LAYER"]
        subgraph QueryPipeline[Query Processing Pipeline]
            QueryRewrite[Query Rewrite]
            CacheCheck[Cache Check]
            IntentDetect[Intent Detect]
            MLRoute[ML Route]
            Escalation[Escalation]
        end
        subgraph MultiAgent[Multi-Agent System - LangGraph]
            Coordinator[Coordinator]
            HRAgent[HR Agent]
            ITAgent[IT Agent]
            SecurityAgent[Security Agent]
            FinanceAgent[Finance Agent]
            ProgressAgent[Progress Agent]
        end
        subgraph RAG[RAG Pipeline]
            SemanticSearch[Semantic Search<br/>ChromaDB]
            BM25Search[BM25 Search]
            RRF[RRF Fusion]
            LLMGen[LLM Generation]
        end
    end

    subgraph Data["DATA LAYER"]
        SQLite[(SQLite<br/>Structured Data)]
        ChromaDB[(ChromaDB<br/>Vectors)]
        MLflow[(MLflow<br/>ML Models)]
    end

    Presentation --> API
    API --> Service
    Service --> Data
```

---

## 2. Data Flow Architecture

```mermaid
flowchart TB
    subgraph Frontend["FRONTEND (Next.js 14)"]
        Components[React Components]
        APIClient[API Client]
        Fetch[HTTP Fetch]
        Components --> APIClient --> Fetch
    end

    subgraph Backend["BACKEND (FastAPI)"]
        MW[Middleware]
        Routes[Routes]
        Services[Services]
        Agents[Agents]
        RAGPipe[RAG]
        LLM[LLM]
        MW --> Routes --> Services --> Agents --> RAGPipe --> LLM
    end

    subgraph DataStores["DATA STORES"]
        SQLite[(SQLite<br/>• Users<br/>• Tasks<br/>• Messages<br/>• Audit Logs)]
        ChromaDB[(ChromaDB<br/>• Embeddings<br/>• Documents<br/>• Metadata)]
        MLflow[(MLflow<br/>• Router Model<br/>• Experiments<br/>• Metrics)]
    end

    Fetch -->|REST API| MW
    Backend --> SQLite
    Backend --> ChromaDB
    Backend --> MLflow
```

---

## 3. LangGraph Multi-Agent State Machine

```mermaid
flowchart TD
    Entry[("ENTRY POINT<br/>coordinator")]
    
    subgraph Routing["CONDITIONAL ROUTING"]
        Decision{Route Decision<br/>Based on: final_department,<br/>multi-intent detection}
    end
    
    Entry --> Decision
    
    HR[HR Agent<br/>🧑‍💼]
    IT[IT Agent<br/>💻]
    Security[Security Agent<br/>🔒]
    Finance[Finance Agent<br/>💰]
    Progress[Progress Agent<br/>📋]
    Multi[Multi-Intent<br/>Parallel Execution<br/>⚡]
    
    Decision -->|HR| HR
    Decision -->|IT| IT
    Decision -->|Security| Security
    Decision -->|Finance| Finance
    Decision -->|Progress/General| Progress
    Decision -->|Multi-Intent| Multi
    
    Finalize[Finalize<br/>Response Wrap]
    
    HR --> Finalize
    IT --> Finalize
    Security --> Finalize
    Finance --> Finalize
    Progress --> Finalize
    Multi --> Finalize
    
    End((END))
    Finalize --> End

    style Entry fill:#4CAF50,color:#fff
    style End fill:#f44336,color:#fff
    style Multi fill:#2196F3,color:#fff
```

---

## 4. RAG Hybrid Retrieval Pipeline

```mermaid
flowchart TD
    Query["USER QUERY<br/>'How do I submit an expense report?'"]
    
    Query --> Parallel
    
    subgraph Parallel["PARALLEL SEARCH EXECUTION"]
        direction LR
        subgraph Semantic["SEMANTIC SEARCH (ChromaDB)"]
            Embed[1. Embed query<br/>768-dim vector]
            VectorSim[2. Vector similarity]
            SemanticTopK[3. Return top-K]
            Embed --> VectorSim --> SemanticTopK
        end
        
        subgraph BM25["KEYWORD SEARCH (BM25)"]
            Tokenize[1. Tokenize query]
            TFIDF[2. TF-IDF scoring]
            BM25TopK[3. Return top-K]
            Tokenize --> TFIDF --> BM25TopK
        end
    end
    
    SemanticTopK --> Fusion
    BM25TopK --> Fusion
    
    subgraph Fusion["RECIPROCAL RANK FUSION (RRF)"]
        Norm1[1. Normalize semantic scores 0-1]
        Norm2[2. Normalize BM25 scores 0-1]
        Combine["3. Combined = 0.7×semantic + 0.3×BM25"]
        Dedup[4. Deduplicate by hash]
        Sort[5. Sort descending]
        Norm1 --> Norm2 --> Combine --> Dedup --> Sort
    end
    
    Fusion --> Chunks
    
    Chunks["TOP-5 DOCUMENT CHUNKS<br/>Relevant policy excerpts"]
    
    Chunks --> LLMGen
    
    subgraph LLMGen["LLM GENERATION (GPT-4o-mini)"]
        System[System: Department instructions]
        Context[Context: Retrieved documents]
        User[User: Original query]
        Response[Generate grounded response]
        System --> Context --> User --> Response
    end

    style Query fill:#E3F2FD,color:#000
    style Response fill:#C8E6C9,color:#000
```

---

## 5. Query Processing Pipeline

```mermaid
flowchart TD
    Start["USER SUBMITS QUERY"]
    
    Step1["STEP 1: LANGUAGE DETECTION<br/>detect_language(message)<br/>Result: 'en' or 'ar'"]
    
    Step2["STEP 2: SEMANTIC CACHE CHECK<br/>1. Compute SHA-256 hash<br/>2. Check exact match<br/>3. Check semantic similarity ≥0.92"]
    
    CacheDecision{Cache Hit?}
    CacheReturn["Return cached response<br/>~50-100ms"]
    
    Step3["STEP 3: MULTI-INTENT DETECTION<br/>intent_detector.detect(message)<br/>+ Keyword scanning"]
    
    IntentDecision{Single or<br/>Multi-Intent?}
    
    Step4A["STEP 4A: SINGLE ROUTING<br/>1. Coordinator classifies<br/>2. Route to agent<br/>3. Agent retrieves + LLM"]
    
    Step4B["STEP 4B: PARALLEL MULTI-AGENT<br/>1. Create tasks per dept<br/>2. Execute in parallel<br/>3. Each agent processes"]
    
    Step5["STEP 5: RAG RETRIEVAL<br/>1. Translate Arabic → English<br/>2. Hybrid search<br/>3. RRF fusion<br/>4. Return top-5 chunks"]
    
    Step6["STEP 6: LLM GENERATION<br/>Model: GPT-4o-mini<br/>Generate response in user's language"]
    
    Step7["STEP 7: COMBINE RESPONSES<br/>(Multi-Intent only)<br/>Add section headers"]
    
    Step8["STEP 8: CACHE RESPONSE<br/>Background thread<br/>Non-blocking"]
    
    Step9["STEP 9: AUDIT LOGGING<br/>Log query, response, routing info"]
    
    Step10["STEP 10: RETURN RESPONSE<br/>{response, message_id, routing}"]
    
    Start --> Step1 --> Step2 --> CacheDecision
    CacheDecision -->|Yes| CacheReturn
    CacheDecision -->|No| Step3
    Step3 --> IntentDecision
    IntentDecision -->|Single| Step4A
    IntentDecision -->|Multi| Step4B
    Step4A --> Step5
    Step4B --> Step5
    Step5 --> Step6
    Step6 --> Step7
    Step7 --> Step8
    Step8 --> Step9
    Step9 --> Step10

    style Start fill:#4CAF50,color:#fff
    style Step10 fill:#2196F3,color:#fff
    style CacheReturn fill:#FF9800,color:#fff
```

---

## 6. Authentication Flow

```mermaid
sequenceDiagram
    participant C as Client
    participant F as FastAPI
    participant D as Database

    C->>F: POST /auth/login<br/>{email, password}
    F->>D: Query user by email
    D-->>F: User record
    
    F->>F: Verify password<br/>(bcrypt.verify)
    
    alt Password Valid
        F->>F: Generate tokens<br/>(access + refresh)
        F-->>C: {access_token,<br/>refresh_token, user}
    else Password Invalid
        F-->>C: 401 Unauthorized
    end

    Note over C,F: Subsequent requests
    C->>F: GET /api/resource<br/>Authorization: Bearer {token}
    F->>F: Validate JWT
    F->>D: Query resource
    D-->>F: Data
    F-->>C: Response
```

---

## 7. Multi-Level Caching Architecture

```mermaid
flowchart TD
    Request["INCOMING REQUEST"]
    
    subgraph L1["LEVEL 1: SEMANTIC CACHE (SQLite)"]
        L1Check["Check:<br/>1. SHA-256 hash exact match<br/>2. Cosine similarity ≥0.92"]
        L1TTL["TTL: 24 hours"]
    end
    
    L1Hit{Hit?}
    L1Return["Return cached LLM response<br/>~50-100ms"]
    
    subgraph L2["LEVEL 2: EMBEDDING CACHE (LRU)"]
        L2Check["Size: 10,000 entries<br/>Skip embedding computation"]
    end
    
    L2Hit{Hit?}
    L2Benefit["~100ms saved"]
    
    subgraph L3["LEVEL 3: HYBRID SEARCH CACHE (TTLCache)"]
        L3Check["Size: 5,000 entries<br/>TTL: 30 minutes<br/>Key: MD5(query+dept+n)"]
    end
    
    L3Hit{Hit?}
    L3Benefit["~200-500ms saved"]
    
    subgraph Pipeline["FULL PIPELINE EXECUTION"]
        Semantic[Semantic Search]
        BM25[BM25 Search]
        RRF[RRF Fusion]
        LLM[LLM Generation]
        Semantic --> BM25 --> RRF --> LLM
    end
    
    Background["BACKGROUND: CACHE POPULATION<br/>Store response (non-blocking)"]
    
    Request --> L1Check --> L1Hit
    L1Hit -->|Yes| L1Return
    L1Hit -->|No| L2Check --> L2Hit
    L2Hit -->|Yes| L2Benefit --> L3Check
    L2Hit -->|No| L3Check
    L3Check --> L3Hit
    L3Hit -->|Yes| L3Benefit --> Pipeline
    L3Hit -->|No| Pipeline
    Pipeline --> Background

    style Request fill:#E3F2FD,color:#000
    style L1Return fill:#C8E6C9,color:#000
    style Pipeline fill:#FFECB3,color:#000
```

---

## 8. Entity Relationship Diagram

```mermaid
erDiagram
    users ||--o{ tasks : has
    users ||--o{ messages : sends
    users ||--o{ feedback : gives
    users ||--o{ user_achievements : earns
    users ||--o{ training_progress : tracks
    users ||--o{ calendar_events : has
    users ||--o{ churn_predictions : receives
    
    messages ||--o| feedback : receives
    
    achievements ||--o{ user_achievements : unlocked_by
    
    training_modules ||--o{ training_progress : tracked_in
    
    workflows ||--o{ workflow_executions : runs
    
    users {
        int id PK
        string name
        string email UK
        string password_hash
        string role
        string department
        enum user_type
        boolean is_active
        date start_date
        string preferred_language
    }
    
    tasks {
        int id PK
        int user_id FK
        enum department
        string title
        text description
        date due_date
        enum status
        datetime completed_at
    }
    
    messages {
        int id PK
        int user_id FK
        text text
        string source
        string language
        datetime timestamp
        json extra_data
    }
    
    achievements {
        int id PK
        string name
        text description
        string icon
        enum category
        int points
        json criteria
    }
    
    user_achievements {
        int id PK
        int user_id FK
        int achievement_id FK
        float progress
        datetime unlocked_at
    }
    
    training_modules {
        int id PK
        string title
        enum department
        json content
        int passing_score
        boolean is_required
    }
    
    training_progress {
        int id PK
        int user_id FK
        int module_id FK
        string status
        int score
        int attempts
    }
    
    feedback {
        int id PK
        int user_id FK
        int message_id FK
        enum feedback_type
        text comment
        boolean routing_was_correct
    }
    
    audit_logs {
        int id PK
        datetime timestamp
        string action
        string resource_type
        int user_id FK
        json details
        string status
    }
```

---

## 9. Internationalization Architecture

```mermaid
flowchart TB
    subgraph Frontend["FRONTEND"]
        subgraph I18nProvider["I18nProvider (Context)"]
            Lang["currentLanguage: 'en' | 'ar'"]
            Trans["translations: Record<string, string>"]
            TFunc["t(key): string"]
            SetLang["setLanguage(lang): void"]
        end
        
        Component["Component uses t('key')<br/>e.g., t('calendar.title')"]
        
        I18nProvider --> Component
    end
    
    API["API Call<br/>GET /api/v1/i18n/{lang}"]
    
    subgraph Backend["BACKEND"]
        I18nService["Translation Service"]
        Translations["Returns:<br/>{ 'calendar.title': 'Calendar', ... }"]
        I18nService --> Translations
    end
    
    Component -->|Fetch translations| API
    API --> I18nService
    Translations -->|JSON response| Component
    
    subgraph Database["DATABASE MULTILINGUAL"]
        TaskModel["Task Model<br/>title, title_ar<br/>description, description_ar"]
        AchModel["Achievement Model<br/>name, name_ar<br/>description, description_ar"]
    end
    
    Backend --> Database

    style Frontend fill:#E3F2FD,color:#000
    style Backend fill:#FFF3E0,color:#000
```

---

## 10. Request Lifecycle

```mermaid
flowchart LR
    subgraph Client["CLIENT"]
        User((User))
    end
    
    subgraph Load["LOAD BALANCER"]
        LB[Nginx/ALB]
    end
    
    subgraph App["APPLICATION"]
        subgraph Middleware["MIDDLEWARE STACK"]
            CORS[CORS]
            Rate[Rate Limit]
            JWT[JWT Auth]
            Audit[Audit]
        end
        
        subgraph Routes["ROUTES"]
            API[FastAPI Routes]
        end
        
        subgraph Services["SERVICES"]
            Auth[Auth Service]
            Chat[Chat Service]
            Task[Task Service]
        end
        
        subgraph Agents["AGENTS"]
            Orch[Orchestrator]
            HR[HR]
            IT[IT]
        end
        
        subgraph RAG["RAG"]
            Search[Hybrid Search]
            Gen[LLM Gen]
        end
    end
    
    subgraph Data["DATA"]
        DB[(SQLite)]
        Vector[(ChromaDB)]
        Cache[(Cache)]
    end
    
    User --> LB --> CORS --> Rate --> JWT --> Audit --> API
    API --> Services --> Agents --> RAG
    RAG --> Data
    Services --> Data

    style User fill:#4CAF50,color:#fff
    style Data fill:#2196F3,color:#fff
```

---

## Agent Communication Flow

```mermaid
sequenceDiagram
    participant U as User
    participant O as Orchestrator
    participant C as Coordinator
    participant A as Specialized Agent
    participant R as RAG Pipeline
    participant L as LLM (GPT-4o-mini)
    
    U->>O: Send query
    O->>O: Check semantic cache
    
    alt Cache Hit
        O-->>U: Return cached response
    else Cache Miss
        O->>C: Route query
        C->>C: ML Classification + Keyword Override
        C-->>O: Department + Confidence
        
        O->>A: Forward to agent (HR/IT/etc.)
        A->>R: Retrieve context
        R->>R: Semantic + BM25 search
        R->>R: RRF fusion
        R-->>A: Top-5 chunks
        
        A->>L: Generate response
        L-->>A: Response text
        A-->>O: AgentResponse
        
        O->>O: Cache response (background)
        O-->>U: Return response
    end
```

---

## Churn Prediction Score Calculation

```mermaid
flowchart LR
    subgraph Inputs["INPUT METRICS"]
        TC[Task Completion<br/>30%]
        AF[Activity Frequency<br/>25%]
        LP[Learning Progress<br/>20%]
        CE[Chat Engagement<br/>15%]
        FS[Feedback Sentiment<br/>10%]
    end
    
    subgraph Calculation["WEIGHTED CALCULATION"]
        Formula["Overall Score =<br/>TC×0.30 + AF×0.25 +<br/>LP×0.20 + CE×0.15 + FS×0.10"]
    end
    
    subgraph Output["RISK LEVEL"]
        Low["LOW (65-100)<br/>🟢"]
        Medium["MEDIUM (45-65)<br/>🟡"]
        High["HIGH (25-45)<br/>🟠"]
        Critical["CRITICAL (0-25)<br/>🔴"]
    end
    
    Inputs --> Calculation --> Output

    style Low fill:#4CAF50,color:#fff
    style Medium fill:#FFEB3B,color:#000
    style High fill:#FF9800,color:#fff
    style Critical fill:#f44336,color:#fff
```

---

## Achievement System Flow

```mermaid
flowchart TD
    Action["USER ACTION<br/>(Complete task, send message, etc.)"]
    
    Check["AchievementService.check_and_unlock(user_id)"]
    
    subgraph Criteria["CHECK CRITERIA TYPES"]
        Tasks["tasks_completed: count"]
        AllTasks["all_tasks_completed"]
        Questions["questions_asked: count"]
        Speed["onboarding_speed: days"]
        Training["all_training_completed"]
        Quiz["quiz_perfect_score"]
        Early["early_completion"]
        Feedback["feedback_given: count"]
    end
    
    Progress{Progress >= 100%?}
    
    Unlock["Unlock Achievement<br/>progress = 100<br/>unlocked_at = now()"]
    
    Update["Update Progress<br/>Store partial progress"]
    
    Notify["Add to unnotified<br/>achievements queue"]
    
    Action --> Check --> Criteria --> Progress
    Progress -->|Yes| Unlock --> Notify
    Progress -->|No| Update

    style Action fill:#E3F2FD,color:#000
    style Unlock fill:#C8E6C9,color:#000
    style Notify fill:#FFECB3,color:#000
```

---

## How to View These Diagrams

### Option 1: GitHub / GitLab
Simply push this file to your repository. GitHub and GitLab automatically render Mermaid diagrams.

### Option 2: VS Code
1. Install extension: **"Markdown Preview Mermaid Support"**
2. Open this file
3. Press `Cmd+Shift+V` (Mac) or `Ctrl+Shift+V` (Windows)

### Option 3: Mermaid Live Editor
1. Go to [mermaid.live](https://mermaid.live)
2. Copy any diagram code (between the ```mermaid and ``` markers)
3. Paste to visualize and export as PNG/SVG

### Option 4: Export to PNG/SVG
Use the Mermaid CLI:
```bash
npm install -g @mermaid-js/mermaid-cli
mmdc -i DIAGRAMS.md -o diagrams/
```

---

*These diagrams complement the [Technical Report](TECHNICAL_REPORT.md) with visual representations of system architecture and data flows.*

