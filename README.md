# 🔭 CodeLens AI

An AI-powered codebase understanding platform. Upload any GitHub repository or ZIP file, then chat with it, trace code flows, analyze architecture, investigate bugs, generate documentation, and visualize dependencies — all grounded in your actual source code via RAG.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (React)                      │
│  Landing → Auth → Dashboard → Workspace                      │
│  Chat · Architecture · Graph · Search · Debug · Docs         │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTP/REST
┌─────────────────────────▼───────────────────────────────────┐
│                    FastAPI Backend                            │
│  /auth  /repositories  /chat  /analyze                       │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │  Processing  │  │   RAG Stack  │  │    Graph Store   │   │
│  │  Pipeline    │  │              │  │                  │   │
│  │  1. Clone    │  │ SentenceXfmr │  │  Neo4j (opt.)    │   │
│  │  2. Parse    │  │ all-MiniLM   │  │  File relations  │   │
│  │  3. Chunk    │  │ ChromaDB     │  │  Import graphs   │   │
│  │  4. Embed    │  │ Groq LLM     │  │                  │   │
│  │  5. Store    │  │ llama3-70b   │  │                  │   │
│  └──────────────┘  └──────────────┘  └──────────────────┘   │
│                                                               │
│  PostgreSQL (users, repos, chats, messages, jobs)            │
└─────────────────────────────────────────────────────────────┘
```

## Project Structure

```
codelens/
├── backend/
│   ├── app/
│   │   ├── api/           # Route handlers
│   │   ├── auth/          # JWT, bcrypt
│   │   ├── config/        # Settings (pydantic-settings)
│   │   ├── database/      # AsyncSQLAlchemy session
│   │   ├── graph/         # Neo4j service
│   │   ├── models/        # SQLAlchemy ORM models
│   │   ├── parsers/       # Code parsing (tree-sitter + regex)
│   │   ├── rag/           # Embeddings, ChromaDB, Groq LLM
│   │   ├── schemas/       # Pydantic request/response schemas
│   │   ├── services/      # GitHub/ZIP ingestion, processing pipeline
│   │   ├── utils/         # Helper functions
│   │   └── main.py        # FastAPI app + lifespan
│   ├── chroma_db/         # Persisted vector store
│   ├── repositories/      # Temp clone directory
│   ├── requirements.txt
│   └── .env               # Local-only secrets; do not commit
│
└── frontend/
    ├── src/
    │   ├── components/
    │   │   └── workspace/ # ChatPanel, ArchitecturePanel, GraphPanel, etc.
    │   ├── context/       # AuthContext
    │   ├── pages/         # Landing, Auth, Dashboard, Workspace, Settings
    │   ├── routes/        # ProtectedRoute
    │   ├── services/      # API client (axios)
    │   ├── App.tsx
    │   └── main.tsx
    └── package.json
```

---

## Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL 14+ (or Supabase)
- Git in PATH
- [Groq API key](https://console.groq.com) (free)

---

## Backend Setup

### 1. Create database

```bash
# Local PostgreSQL
createdb codelens

# Or use Supabase (free tier) — copy the connection string
```

### 2. Install dependencies

```bash
cd codelens/backend
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
```

Edit `backend/.env`:

```env
GROQ_API_KEY=your_key_here
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/codelens
DATABASE_URL_SYNC=postgresql://postgres:password@localhost:5432/codelens
JWT_SECRET=run_openssl_rand_hex_32_and_paste_here
```

### 4. Start backend

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Tables are created automatically on first start.

API docs: http://localhost:8000/docs

---

## Frontend Setup

```bash
cd codelens/frontend
npm install
npm run dev
```

Open: http://localhost:5173

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/signup` | Create account |
| POST | `/api/v1/auth/login` | Login, get JWT |
| GET  | `/api/v1/auth/me` | Current user |
| POST | `/api/v1/repositories/github` | Index GitHub repo |
| POST | `/api/v1/repositories/zip` | Index ZIP upload |
| GET  | `/api/v1/repositories` | List user's repos |
| GET  | `/api/v1/repositories/:id/status` | Processing status |
| POST | `/api/v1/chat/:repoId/message` | Send chat message |
| GET  | `/api/v1/chat/:repoId/chats` | List chats |
| POST | `/api/v1/analyze/architecture` | Analyze architecture |
| POST | `/api/v1/analyze/flow` | Trace code flow |
| POST | `/api/v1/analyze/bug` | Investigate bug |
| POST | `/api/v1/analyze/documentation` | Generate README |
| POST | `/api/v1/analyze/onboarding` | Generate onboarding guide |
| GET  | `/api/v1/analyze/graph/:repoId` | Dependency graph |
| POST | `/api/v1/analyze/search` | Semantic code search |

---

## RAG Pipeline

```
Repository
  └─► File Scanner (supported: .py .js .ts .tsx .jsx .java)
        └─► Code Parser (regex AST extraction: functions, classes, imports)
              └─► Semantic Chunker (1000 chars, 200 overlap + context headers)
                    └─► SentenceTransformer (all-MiniLM-L6-v2, normalized)
                          └─► ChromaDB (cosine similarity, persistent)
                                └─► Query: embed → top-7 chunks → Groq prompt
                                      └─► llama3-70b-8192 → grounded answer
```

---

## Neo4j (Optional)

Neo4j enables full dependency graph visualization and Graph RAG.

```env
NEO4J_ENABLED=true
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
```

Use [Neo4j Aura Free](https://neo4j.com/cloud/platform/aura-graph-database/) for a cloud-hosted option.

When disabled (default), dependency graphs are built from the PostgreSQL `repository_files` table using import analysis.

---

## Deployment

### Backend → Render

1. Create a new Web Service on [Render](https://render.com)
2. Set root to `backend/`
3. Build: `pip install -r requirements.txt`
4. Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add all `.env` values as environment variables

### Frontend → Vercel

1. Import repo on [Vercel](https://vercel.com)
2. Set root to `frontend/`
3. Add env var: `VITE_API_BASE_URL=https://your-backend.onrender.com`
4. The client automatically appends `/api/v1` for production requests

### Database → Supabase

1. Create a project on [Supabase](https://supabase.com)
2. Copy the PostgreSQL connection string
3. Use as `DATABASE_URL` (replace `postgres://` with `postgresql+asyncpg://`)

---

## Environment Variables

Use `backend/.env` for backend secrets and `frontend/.env` for browser-safe frontend values.

| Variable | Put it in | Where it comes from | What it does |
|----------|-----------|---------------------|--------------|
| `GROQ_API_KEY` | `backend/.env` | Groq Console > API keys | LLM requests for chat and analysis |
| `DATABASE_URL` | `backend/.env` | Supabase or your PostgreSQL host | Async database connection |
| `DATABASE_URL_SYNC` | `backend/.env` | Supabase or your PostgreSQL host | Migrations and sync jobs |
| `JWT_SECRET` | `backend/.env` | Generate locally with `secrets.token_hex(32)` | Signs user JWTs |
| `SUPABASE_URL` | `backend/.env` | Supabase Project Settings > API | Supabase project endpoint |
| `SUPABASE_KEY` | `backend/.env` | Supabase Project Settings > API | Supabase anon key |
| `SUPABASE_SERVICE_ROLE_KEY` | `backend/.env` | Supabase Project Settings > API | Privileged server access |
| `FIREBASE_PROJECT_ID` | `backend/.env` | Firebase Console > Project settings | Firebase admin auth |
| `FIREBASE_PRIVATE_KEY` | `backend/.env` | Firebase service account JSON | Firebase admin auth |
| `FIREBASE_CLIENT_EMAIL` | `backend/.env` | Firebase service account JSON | Firebase admin auth |
| `STRIPE_SECRET_KEY` | `backend/.env` | Stripe Dashboard > Developers > API keys | Payment API access |
| `STRIPE_WEBHOOK_SECRET` | `backend/.env` | Stripe Dashboard > Webhooks | Verifies Stripe webhooks |
| `STRIPE_PRICE_ID_PRO` | `backend/.env` | Stripe Dashboard > Products | Monthly plan price |
| `STRIPE_PRICE_ID_PRO_YEARLY` | `backend/.env` | Stripe Dashboard > Products | Yearly plan price |
| `R2_ACCOUNT_ID` | `backend/.env` | Cloudflare Dashboard > R2 | R2 bucket account |
| `R2_ACCESS_KEY_ID` | `backend/.env` | Cloudflare R2 API tokens | R2 access key |
| `R2_SECRET_ACCESS_KEY` | `backend/.env` | Cloudflare R2 API tokens | R2 secret key |
| `GITHUB_CLIENT_ID` | `backend/.env` | GitHub Developer Settings > OAuth Apps | GitHub OAuth login |
| `GITHUB_CLIENT_SECRET` | `backend/.env` | GitHub Developer Settings > OAuth Apps | GitHub OAuth login |
| `NEO4J_URI` | `backend/.env` | Neo4j Aura or local Neo4j | Optional graph database |
| `NEO4J_USER` | `backend/.env` | Neo4j Aura or local Neo4j | Neo4j login |
| `NEO4J_PASSWORD` | `backend/.env` | Neo4j Aura or local Neo4j | Neo4j login |
| `VITE_API_BASE_URL` | `frontend/.env` | Your deployed backend URL | Tells the frontend where the API lives |
| `VITE_FIREBASE_API_KEY` | `frontend/.env` | Firebase Console > Project settings > Web app | Firebase browser auth |
| `VITE_FIREBASE_AUTH_DOMAIN` | `frontend/.env` | Firebase Console > Project settings > Web app | Firebase browser auth |
| `VITE_FIREBASE_PROJECT_ID` | `frontend/.env` | Firebase Console > Project settings > Web app | Firebase browser auth |
| `VITE_FIREBASE_STORAGE_BUCKET` | `frontend/.env` | Firebase Console > Project settings > Web app | Firebase browser auth |
| `VITE_FIREBASE_MESSAGING_SENDER_ID` | `frontend/.env` | Firebase Console > Project settings > Web app | Firebase browser auth |
| `VITE_FIREBASE_APP_ID` | `frontend/.env` | Firebase Console > Project settings > Web app | Firebase browser auth |
| `VITE_STRIPE_PUBLISHABLE_KEY` | `frontend/.env` | Stripe Dashboard > Developers > API keys | Stripe checkout in the browser |
| `VITE_POSTHOG_API_KEY` | `frontend/.env` | PostHog project settings | Browser analytics |

If you only want the minimum working deployment, fill these first: `GROQ_API_KEY`, `DATABASE_URL`, `DATABASE_URL_SYNC`, `JWT_SECRET`, and `VITE_API_BASE_URL`. The optional services can stay blank until you actually use them.

---

## Example Usage

1. **Sign up** at `http://localhost:5173/signup`
2. **Add Repository** → paste `https://github.com/tiangolo/fastapi`
3. Wait ~60s for processing (status bar in dashboard)
4. **Open Workspace** → Chat tab
5. Ask: *"How does dependency injection work in FastAPI?"*
6. See grounded answer with file citations and source chunks
7. Switch to **Architecture** → click "Analyze Architecture"
8. Switch to **Debug** → paste a stack trace for root cause analysis
