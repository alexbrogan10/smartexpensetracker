# Smart Expense Tracker

A full-stack personal finance application for tracking income and expenses, managing budgets and savings goals, and surfacing AI-powered spending insights — built as a production-quality portfolio project.

> **Status:** early scaffold (Milestone 1 of 14). This README will be expanded with full setup, screenshots, and feature documentation as the project progresses — see [`docs/`](./docs) for architecture notes as they're added.

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
├── docker/        # Shared Docker assets
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

This starts PostgreSQL, the backend API, and the frontend together.

## Environment Variables

Copy `.env.example` to `.env` at the project root and adjust as needed. See that file for the full list of variables (database connection, JWT secret, CORS origins, frontend API base URL).

## Running Tests

```bash
# Backend
cd backend
pytest

# Frontend (added in a later milestone)
cd frontend
npm test
```

## Roadmap

This project is being built incrementally across 14 milestones — project setup, database design, authentication, transaction/budget management, dashboard & analytics, CSV import, AI categorization, forecasting, anomaly detection, and finally testing, Docker/CI, and documentation polish. Progress and architectural decisions are tracked in [`docs/`](./docs) as each milestone lands.

## License

TBD.
