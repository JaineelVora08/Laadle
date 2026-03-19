# BEACON

**Peer Mentoring Platform** — Connecting students with experienced seniors through intelligent matching, trust-scored advice, and AI-augmented query resolution.

## Architecture

| Layer | Technology |
|-------|-----------|
| Backend | Django 4.2 + Django REST Framework |
| Graph DB | Neo4j 5 (via neomodel) |
| Vector DB | Pinecone |
| SQL DB | PostgreSQL 15 |
| Task Queue | Celery + Redis |
| AI/LLM | OpenAI API |
| Frontend | React 18 + Vite + Zustand |

## Modules

1. **Auth & User Profile Service** — Registration, login, JWT auth, profile management, achievement tracking
2. **Domain & Mentor Matching Service** — Domain graph (Neo4j), embedding-based domain linking, 2-hop mentor/peer matching
3. **Query Orchestrator & AI Services** — Query pipeline, RAG engine, conflict detection, LLM synthesis, follow-up generation
4. **Adaptive Scheduler** — Load balancing, cold-start broadcasting via Celery tasks

## Quick Start

```bash
# 1. Copy environment variables
cp .env.example .env

# 2. Start all services
docker-compose up -d

# 3. Run migrations
docker-compose exec backend python manage.py migrate

# 4. Install frontend dependencies
cd frontend && npm install && npm run dev
```

## Project Structure

```
beacon/
├── backend/          # Django project
│   ├── beacon/       # Django settings, urls, wsgi
│   └── apps/         # Service modules
│       ├── auth_service/
│       ├── user_profile_service/
│       ├── domain_management_service/
│       ├── mentor_matching_service/
│       ├── trust_score_service/
│       ├── query_orchestrator/
│       ├── ai_services/
│       └── adaptive_scheduler_service/
├── frontend/         # React + Vite app
│   └── src/
│       ├── api/      # Axios API modules
│       ├── store/    # Zustand state stores
│       ├── pages/    # Route-level components
│       └── components/ # Reusable UI components
└── shared/
    └── schemas.md    # JSON API contracts
```

## API Contracts

See [shared/schemas.md](shared/schemas.md) for all request/response JSON shapes.

## Environment Variables

See [.env.example](.env.example) for all required configuration.
