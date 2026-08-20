# Smart Expense Tracker

[![CI](https://github.com/alexbrogan10/smartexpensetracker/actions/workflows/ci.yml/badge.svg)](https://github.com/alexbrogan10/smartexpensetracker/actions/workflows/ci.yml)

A full-stack personal finance application for tracking income and expenses, managing budgets and savings goals, and surfacing AI-powered spending insights — built as a production-quality portfolio project.

> **Status:** Milestone 13 of 14 complete (Docker, Docker Compose, and CI). Full setup narrative, screenshots, and feature documentation land in the final documentation milestone — see [`docs/`](./docs) for architecture notes as they're added.

## Tech Stack

**Backend:** Python 3.13, FastAPI, SQLAlchemy, Alembic, PostgreSQL, Pydantic, Pandas, Scikit-learn, Uvicorn
**Frontend:** React, TypeScript, Vite, Material UI, React Router, Axios, Recharts
**Auth:** JWT, bcrypt
**Testing:** pytest, React Testing Library
**DevOps:** Docker, Docker Compose, GitHub Actions

## Project Structure

```
smart-expense-tracker/
├── backend/       # FastAPI application (app/, tests/, alembic/)
├── frontend/      # React + TypeScript SPA (Vite)
├── docs/          # Architecture, database, API, and deployment docs
├── scripts/       # Dev/ops helper scripts
├── sample_data/   # Fictional seed data for local demos
└── docker-compose.yml
```

## Getting Started (local development)

### Prerequisites

- Python 3.13
- Node.js 22+
- Docker & Docker Compose (optional, for running Postgres / the full stack)

### Backend

```bash
cd backend
python3.13 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Make sure PostgreSQL is running and DATABASE_URL (see .env.example) points at it,
# then apply migrations:
alembic upgrade head

uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`, with a health check at `GET /health`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The app will be available at `http://localhost:5173`.

### Full stack via Docker Compose

```bash
cp .env.example .env
docker compose up --build
```

This starts PostgreSQL, the backend API, and the frontend together. The backend
container applies Alembic migrations automatically on startup (via
`backend/docker-entrypoint.sh`) before the API starts serving, so a fresh
`docker compose up` always boots against an up-to-date schema. The backend
exposes a Docker `HEALTHCHECK` against `GET /health`, which the frontend
service waits on before starting.

To point the frontend at a different backend URL (e.g. deploying beyond
localhost), set `VITE_API_BASE_URL` in `.env` before building — Vite inlines
it into the built JS at image-build time, so it can't be changed later at
container-run time without rebuilding the image.

## Environment Variables

Copy `.env.example` to `.env` at the project root and adjust as needed. See that file for the full list of variables (database connection, JWT secret, CORS origins, frontend API base URL).

## Running Tests

```bash
# Backend (requires a running PostgreSQL instance for API/integration tests)
cd backend
pytest
pytest --cov=app --cov-report=term-missing  # with coverage

# Frontend
cd frontend
npm test                # run once
npm run test:watch      # watch mode
npm run test:coverage   # with coverage
```

## Continuous Integration

Every push and pull request runs the [CI workflow](./.github/workflows/ci.yml):
a backend job (ruff lint/format, `alembic upgrade head` against a real
PostgreSQL service container, then pytest with coverage), a frontend job
(eslint, prettier, `tsc -b`, vitest, `vite build`), and a job that builds both
Docker images to catch any Dockerfile regressions.

## Roadmap

This project is being built incrementally across 14 milestones — project setup, database design, authentication, transaction/budget management, dashboard & analytics, CSV import, AI categorization, forecasting, anomaly detection, and finally testing, Docker/CI, and documentation polish. Progress and architectural decisions are tracked in [`docs/`](./docs) as each milestone lands.

## License

TBD.
