# FlowBoard Plan

## Stages
1. Stage 1 - Project init and scaffolding
2. Stage 2 - Backend core (FastAPI, config, db, health, tests)
3. Stage 3 - Models, Alembic, repositories, seed data, tests
4. Stage 4 - Boards, columns, tasks API with events and tests
5. Stage 5 - RabbitMQ abstraction and domain events with tests
6. Stage 6 - Worker and automation rules with tests
7. Stage 7 - Notifications and incoming tasks with tests
8. Stage 8 - WebSocket realtime with tests
9. Stage 9 - Frontend foundation and global styles
10. Stage 10 - Kanban UI, DnD, task modal, API integration
11. Stage 11 - Realtime updates, admin panels, notifications UI
12. Stage 12 - Docker hardening, Docs, final report

## Risks
- 100% coverage target may require extra mocks and branch tests
- External dependencies (Postgres/RabbitMQ) may be unavailable locally
- Event-driven flow must stay consistent across API and worker
- Realtime + DnD UI can introduce edge cases
