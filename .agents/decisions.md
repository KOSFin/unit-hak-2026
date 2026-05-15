# Architecture Decisions

- FastAPI for async-ready API, clear typing, and solid test ergonomics
- React + Vite + CSS Modules for fast iteration and scoped styles
- RabbitMQ for reliable queue semantics and event-driven flow
- Separate worker service to isolate automation and async processing
- No Tailwind to meet custom design constraints
- No full auth in hackathon scope; keep JWT_SECRET for future extension
