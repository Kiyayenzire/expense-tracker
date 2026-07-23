# ETA Expense Tracker

A Docker-based full stack expense tracker application built with:

- Backend: Django 4.2 + Django REST Framework
- Frontend: React + Vite
- Database: PostgreSQL
- Task queue: Celery + Redis
- Authentication: Django AllAuth + dj-rest-auth with custom user model
- Currency handling: Weekly exchange rates, converter API, multi-currency support
- Reporting: daily/weekly/monthly/quarterly/yearly summaries, predictions, anomaly detection
- Export: report exports via API
- UI: Bootstrap, Material UI icon support, Font Awesome, light/dark theme
- Containerization: Docker + Docker Compose
- CI/CD: GitHub Actions and GitHub Container Registry (GHCR)

## What is included

- `backend/` — Django application with `accounts` and `expenses` apps.
- `frontend/` — React application built with Vite.
- `docker-compose.dev.yml` — development compose stack with live code mounts.
- `docker-compose.prod.yml` — production-ready compose stack with Postgres, Redis, backend, frontend, and Nginx.
- `.env.dev`, `.env.prod`, and root `.env` sample environment support.
- `backend/requirements/base.txt`, `dev.txt`, `prod.txt` for dependency separation.
- `frontend/package-lock.json` for stable frontend dependencies.
- `backend/tests/unit`, `backend/tests/integration`, `backend/tests/e2e` for pytest-based testing.
- `backend/expenses/services/` — clean service layer for predictions, currency conversion, and reporting.

## Key capabilities

- Custom Django user model with admin/user roles.
- Login page that authenticates against Django REST endpoints.
- Expense entry with date, category, item, supplier/provider, country, quantity, currency, notes, local user time, and timezone.
- Stored entry currency and weekly exchange rates for historical integrity.
- Default currency display is Euro, with USD and UGX support.
- Predictive spending using past expenses and simple moving average logic.
- Anomaly detection for unusual expense spikes.
- Exportable monthly and annual reports.
- European date formatting everywhere.
- Dark/light mode toggle.

## Prerequisites

This project is designed to run entirely in Docker. The only required host dependencies are:

- Docker
- Docker Compose
- Git

If you want to run frontend build locally or inspect package locks, Node.js and npm are also helpful.

## Environment files

- `.env.dev` — development environment values.
- `.env.prod` — production environment values.
- `.env` — local development copy loaded by Docker Compose and Django.
- `frontend/.env` — frontend Vite dev environment settings.
- `frontend/.env.production` — frontend production build environment.

> Do not commit secret values to version control. Keep `.env` and `.env.prod` secure and use your own keys in production.

## Running locally with Docker

1. Copy `.env.dev` to `.env` if you need default local values:

```bash
cp .env.dev .env
```

2. Bring up the development stack:

```bash
docker compose -f docker-compose.dev.yml up --build
```

3. Open the frontend at `http://localhost:5173`.
4. Django API runs at `http://localhost:8000/api`.

### Seed initial data

From inside the backend container, you can seed categories, items, currencies, and exchange rates with:

```bash
docker compose -f docker-compose.dev.yml exec backend python manage.py seed_initial_data
```

### Create a superuser

```bash
docker compose -f docker-compose.dev.yml exec backend python manage.py createsuperuser
```

## Production deployment

Use `docker-compose.prod.yml` and environment variables from `.env.prod`.

```bash
docker compose -f docker-compose.prod.yml up --build
```

The production stack uses Nginx as a reverse proxy defined in `nginx/nginx.prod.conf`:

- `/api/` is routed to the Django backend container.
- `/` is routed to the frontend static container.

## Backend dependency structure

- `backend/requirements/base.txt` — runtime dependencies.
- `backend/requirements/dev.txt` — development tools and test libraries.
- `backend/requirements/prod.txt` — production dependencies.

## Frontend dependencies

- React 18
- Vite
- Bootstrap 5
- Material UI icons
- Font Awesome icons
- Recharts
- Axios

## Testing

Run backend tests with pytest inside the backend container or locally if Python is available.

```bash
cd backend
python -m pytest -q
```

The repository includes structured tests for:

- `backend/tests/unit` — unit tests
- `backend/tests/integration` — integration tests
- `backend/tests/e2e` — end-to-end workflows

## CI/CD

A GitHub Actions workflow is configured at `.github/workflows/ci.yml`.

The workflow:

- installs backend Python dependencies
- runs pytest
- installs frontend dependencies
- builds the React app
- on `main` branch pushes, builds and pushes backend and frontend Docker images to GHCR

### Publishing to GitHub Container Registry

The workflow uses `ghcr.io/${{ github.repository_owner }}/expense-tracker-backend` and `ghcr.io/${{ github.repository_owner }}/expense-tracker-frontend`.

> Ensure package permissions are enabled for GitHub Packages and the `GITHUB_TOKEN` has package write access.

## DigitalOcean deployment strategy

Recommended production deployment path:

1. Create a Droplet or App Platform service.
2. Install Docker and Docker Compose on the Droplet.
3. Copy your application repository to the server.
4. Create a production `.env.prod` file with your PostgreSQL, Redis, and Fixer API credentials.
5. Run:

```bash
docker compose -f docker-compose.prod.yml up --build -d
```

For higher availability, use DigitalOcean Managed PostgreSQL and Redis, then update your environment variables to point to the managed services.

## Currency APIs and premium services

The project supports a currency conversion API. The default integration is designed for Fixer.io.

- Fixer.io: premium plans start at around $10/month for basic exchange rate data.
- Alternative free APIs:
  - exchangerate.host
  - openexchangerates.org (limited free tier)
  - Frankfurter API

## Recommended open source and free tools

- Django + Django REST Framework
- PostgreSQL
- Redis
- Celery
- React + Vite
- Bootstrap
- Font Awesome
- GitHub Actions

## Suggested commercial upgrades

- Fixer.io for premium currency data: starts at around $10/month.
- Auth0 for full 2FA and enterprise authentication: free developer tier, paid plans for production.
- DigitalOcean Managed Databases: PostgreSQL and Redis pricing starts around $15/month for basic plans.
- Cloudflare or DigitalOcean Load Balancer for production traffic.

## Notes on mobile app support

This repository is web-first, but the API backend is designed to support mobile clients as well.

- A mobile app for iOS/Android can be built using React Native or Expo.
- The same endpoints can serve mobile app login, expense entry, reporting, and predictions.

## European date formatting

The frontend formats dates as `DD/MM/YYYY` and stores both:

- the user-local timestamp for the entry
- the timezone for data integrity

## Important files and directories

- `backend/backend/settings.py` — Django settings and environment loading.
- `backend/expenses/models.py` — domain models for expense, category, currency, and conversions.
- `backend/expenses/services/` — business logic for predictions, summaries, reporting, currency conversion.
- `frontend/src/components` — login and dashboard UI.
- `docker-compose.dev.yml` — developer compose stack.
- `docker-compose.prod.yml` — production compose stack.
- `.github/workflows/ci.yml` — GitHub Actions CI/CD.

## How to use

1. Start Docker.
2. Create `.env` from `.env.dev`.
3. Run `docker compose -f docker-compose.dev.yml up --build`.
4. Seed initial data and create a superuser.
5. Open `http://localhost:5173` and login.

If you need a token-based login for API access, use the `/api/auth/login/` endpoint with your username and password.

## Final note

This project is intentionally built to be container-first so you can evaluate it without installing Python, PostgreSQL, Redis, or Node directly on your machine.
