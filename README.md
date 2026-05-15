# FlowBoard

> Event-driven Kanban task management system with real-time WebSocket sync and automation rules.

## Stack

| Layer | Technology |
|---|---|
| Backend API | FastAPI + SQLAlchemy 2 + PostgreSQL |
| Event Bus | RabbitMQ (amq.fanout exchange) |
| Automation Worker | Standalone Python process |
| Real-time | WebSocket (native FastAPI) |
| Frontend | React 19 + Vite + CSS Modules |
| Reverse Proxy | Nginx (Alpine) |
| Infrastructure | Docker Compose |

## Quick Start

```bash
cp .env.example .env
# Edit .env to set secrets, then:
docker compose up --build
```

- Frontend: http://localhost:3000  
- Backend API docs: http://localhost:8000/docs  
- RabbitMQ Management: http://localhost:15672

## Development (no Docker)

### Backend
```bash
cd Backend
python -m venv ../venv
source ../venv/bin/activate
pip install -e ".[dev]"

# Run migrations
alembic upgrade head

# Start API
uvicorn app.main:app --reload --port 8000

# Start automation worker (separate terminal)
python -m app.worker

# Tests (100% coverage enforced)
pytest --cov=app --cov-report=term-missing --cov-fail-under=100
```

### Frontend
```bash
cd Frontend
nvm use --lts
npm install
npm run dev    # http://localhost:5173
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                       Browser                           │
│          React SPA ←─WebSocket──────────────────────┐   │
└──────────────┬──────────────────────────────────────│───┘
               │ HTTP                                  │
        ┌──────▼─────┐       ┌──────────────────────┐ │
        │  FastAPI   │──────►│    RabbitMQ fanout   │─┘
        │  REST API  │       │      exchange         │
        └──────┬─────┘       └──────────┬───────────┘
               │                        │
        ┌──────▼─────┐       ┌──────────▼───────────┐
        │ PostgreSQL │       │  Automation Worker   │
        └────────────┘       └──────────────────────┘
```

**Event flow:**
1. Client creates/moves a task via REST API.
2. API publishes a `DomainEvent` to the `amq.fanout` exchange.
3. **Worker** consumes from `task_events` queue, evaluates `AutomationRule` conditions, and calls back into the API to apply actions (e.g. auto-update task status).
4. **WS Consumer** (in-process thread) receives the same events via an exclusive fanout queue and broadcasts them to all connected WebSocket clients for that board, triggering a live refresh.

## API Reference

See http://localhost:8000/docs for full interactive Swagger UI.

Key endpoints:

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Liveness probe |
| GET | `/ready` | Readiness probe (checks DB+MQ) |
| GET/POST | `/api/boards` | List / create boards |
| GET/POST | `/api/boards/{id}/columns` | Columns |
| GET/POST | `/api/boards/{id}/tasks` | Tasks |
| POST | `/api/boards/{id}/tasks/{tid}/move` | Move task (triggers event) |
| GET/PATCH | `/api/notifications/{id}/read` | Notifications |
| GET/PATCH | `/api/incoming-tasks/{id}/accept` | Incoming tasks |
| WS | `/ws/{board_id}?token=...` | Real-time board stream |

## Testing

```bash
cd Backend
pytest --cov=app --cov-report=term-missing --cov-fail-under=100
```

100% coverage is enforced via CI (`--cov-fail-under=100`).
