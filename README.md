# ETA Expense Tracker

ETA is a full-stack personal and household expense tracker built with Django REST Framework and React. It is designed for multi-currency tracking, reporting, profile management, and AI-style financial insights while keeping the app lightweight and easy to run in Docker.

## Highlights

- Multi-currency expense tracking with EUR, USD, and UGX support
- Historical exchange-rate conversion by expense date
- User-scoped data, profile images, and monthly income support
- Dashboard summaries and spending trends by category and date
- CSV and PDF report exports for monthly, yearly, custom-range, and single-period views
- Natural-language quick expense entry with review before save
- Spending prediction, anomaly detection, budget recommendations, and financial insight cards
- Light and dark theme support with a consistent grey/silver default light theme
- No payment feature is implemented

## Stack

- Backend: Django 4.2, DRF, Celery, Redis
- Frontend: React + Vite + Recharts
- Database: PostgreSQL via Docker Compose
- Authentication: custom Django user model with token auth and profile API endpoints
- Containerization: Docker Compose
- Testing: pytest for backend and Vitest/Playwright for frontend

## Repository layout

- `eta_backend/` — Django project and API
- `eta_backend/accounts/` — user model, profile serializer, login/profile APIs
- `eta_backend/expenses/` — expense models, services, views, report generation
- `eta_frontend/` — Vite React app
- `nginx/` — reverse-proxy configuration for production-style hosting
- `docker-compose.yml` — main local stack
- `docker-compose.override.yml` — development overrides for live file mounts
- `docker-compose.test.yml` — isolated test stack
- `.env.dev` — default local development environment file
- `.env` — optional root env file used by the Docker stack

## Prerequisites

- Docker
- Docker Compose
- Git
- Optional for local frontend work: Node.js and npm

## Quick start

1. Ensure the project root contains a working `.env.dev` file.
2. Start the stack:

```bash
docker compose --env-file .env.dev up -d --build
```

3. Open the app:
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000/api

4. Create an admin or superuser if required:

```bash
docker compose --env-file .env.dev exec backend python manage.py createsuperuser
```

5. Open the admin panel at:

```text
http://127.0.0.1:8000/etaalthech2026/
```

## Environment configuration

The current project expects a root `.env` file or a `.env.dev` file for local runs, as configured in the Django settings and compose files.

The default development values are stored in `.env.dev` and include:

- PostgreSQL connection settings
- Redis and Celery URLs
- Django secret key and allowed hosts
- default currency as EUR
- custom admin URL `etaalthech2026`
- frontend base URL

Do not commit real secrets to version control. For production, use a secure `.env` or `.env.prod` file and keep API keys out of source control.

## Core features

- Custom user profile with avatar upload and monthly income
- Expense creation, edits, filtering, and date-based reporting
- Category and item tracking for spending trends
- Spending prediction and budget guidance based on real historical data
- Insight modules for natural-language entry, anomaly detection, and financial guidance
- CSV and PDF export flows for selected periods and custom date ranges
- User-specific data isolation so each account only sees its own entries

## Admin and access

The project uses a custom admin route set by `DJANGO_ADMIN_URL`.

In the default local setup this is:

```text
http://127.0.0.1:8000/etaalthech2026/
```

Use this route for direct Django admin access and currency-rate management.

## Running tests

Backend tests:

```bash
docker compose --env-file .env.dev exec backend pytest -q
```

Targeted backend runs are also supported, for example:

```bash
docker compose --env-file .env.dev exec backend pytest tests/unit -q
docker compose --env-file .env.dev exec backend pytest tests/integration -q
docker compose --env-file .env.dev exec backend pytest tests/e2e -q
```

Frontend tests:

```bash
cd eta_frontend
npm test
```

Frontend browser tests:

```bash
cd eta_frontend
npm run test:e2e
```

## Production setup

Use the root `docker-compose.yml` stack with a production-ready environment file:

```bash
docker compose --env-file .env up -d --build
```

If using Nginx in front of the app, the project includes configuration under `nginx/` and the stack wires web traffic through the reverse proxy.

## Local development notes

- The frontend runs in Vite on port 5173.
- The backend runs Django on port 8000.
- Redis handles Celery messaging and background tasks.
- PostgreSQL is used as the primary database.
- Celery worker and Celery beat run as part of the same Docker stack.

## Important implementation notes

- The custom profile picture field is optional; a default avatar is used when a user has not uploaded one.
- Monthly income is stored on the user and is used in budget recommendation logic.
- Report exports use the actual reporting period label, including month names in file output.
- User data is intentionally isolated by account.
- Payment functionality is intentionally not included in this codebase.

## Troubleshooting

### Frontend not loading

- Validate that Docker services are running:

```bash
docker compose --env-file .env.dev ps
```

- Check container logs:

```bash
docker compose --env-file .env.dev logs -f frontend backend
```

### Backend issues

```bash
docker compose --env-file .env.dev exec backend python manage.py check
docker compose --env-file .env.dev exec backend python manage.py migrate
```

### Reset local stack

```bash
docker compose --env-file .env.dev down -v
```

Then start again with:

```bash
docker compose --env-file .env.dev up -d --build
```

## Contribution and support

This repository is intended for local development and deployment with Docker. The documented setup reflects the actual project configuration currently in this workspace, and the commands above should be used rather than older references to non-existent `docker-compose.dev.yml` or `docker-compose.prod.yml` files.

## License

The repository does not currently declare a formal license file. Check the project root for the active legal or deployment requirements before publishing or redistributing it externally.



1. Start Docker.
2. Create `.env` from `.env.dev`.
3. Run `docker compose -f docker-compose.dev.yml up --build`.
4. Seed initial data and create a superuser.
5. Open `http://localhost:5173` and login.

If you need a token-based login for API access, use the `/api/auth/login/` endpoint with your username and password.

## Final note

This project is intentionally built to be container-first so you can evaluate it without installing Python, PostgreSQL, Redis, or Node directly on your machine.
