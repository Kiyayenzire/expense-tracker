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
   - Frontend: http://localhost:5174
   - Backend API: http://localhost:8002/api

4. Create a Django superuser if required:

```bash
docker compose --env-file .env.dev exec backend python manage.py createsuperuser
```

5. Open the admin panel at:

```text
http://127.0.0.1:8002/etaalthech2026/
```

Django Admin is restricted to superusers. Each Admin session must be established through the Admin login form with a username and password; an app password session or Google/Apple sign-in session alone does not grant Admin access.
Admin sessions expire after 11 minutes without mouse, keyboard, touch, scroll, or Admin request activity. This timeout applies only to Django Admin; regular application sessions are unchanged.

## Environment configuration

The current project expects a root `.env` file or a `.env.dev` file for local runs, as configured in the Django settings and compose files.

The default development values are stored in `.env.dev` and include:

- PostgreSQL connection settings
- Redis and Celery URLs
- Django secret key and allowed hosts
- default currency as EUR
- custom admin URL `etaalthech2026`
- frontend base URL
- mandatory email verification for password registration
- optional support contact settings (`SUPPORT_EMAIL`, `SUPPORT_PHONE`)

Do not commit real secrets to version control. For production, use a secure `.env` or `.env.prod` file and keep API keys out of source control.

## Account verification and social sign-in

Password registrations remain inactive until the user opens the verification link sent to their email. In development, `.env.dev` uses Django's console email backend, so the message is printed in the backend container logs. Production uses the configured `EMAIL_BACKEND` and SMTP settings from the production environment.

Google and Apple sign-in are optional and must be configured separately in each environment's database. Password-based registration and sign-in do not depend on these providers.

When the login screen loads, it requests `GET /api/auth/options/`. A provider is reported as configured when a Django Social Application for that provider is associated with the Site whose ID is `SITE_ID` (default `1`). This check confirms the database record and Site association only; it does not test the credentials or the provider's OAuth callback. If the request itself fails, the login screen reports that availability could not be checked instead of claiming the provider is unconfigured.

To enable a provider in local development, staging, or production:

1. Create OAuth credentials in the provider's developer console and register the callback URL for that environment. Use the matching URLs below:

```text
http://localhost:8002/accounts/google/login/callback/
http://localhost:8002/accounts/apple/login/callback/
https://eta.althech.com/accounts/google/login/callback/
https://eta.althech.com/accounts/apple/login/callback/
```

2. Open that environment's Django Admin and go to **Social Accounts > Social Applications**. Add a Google or Apple application with the credentials from the provider. Do not commit OAuth secrets to the repository.
3. In the application's **Sites** field, select the Site record with ID matching `SITE_ID` for that environment, then save. Each environment has its own database and must be configured independently. The Site domain should match the environment's public host.
4. Check `GET /api/auth/options/` for that environment. The selected provider should have `"configured": true`. Then complete a real sign-in to verify the credentials and callback with the provider.

For local development, the admin URL is `http://localhost:8002/etaalthech2026/`. A `true` readiness value alone does not prove the provider credentials or callback are valid; if OAuth redirects fail after that check, verify the provider console credentials and exact callback URL.

### Social accounts, passwords, and linking

A social sign-up creates a normal application user and a separate allauth `SocialAccount` link. The social account is identified by its provider and provider user ID; adding a local password does not remove that link. In the Profile page, a social-only user can create a password after their email is verified. The existing **Forgot Password** flow can also set a password while signed out. Both methods update the same user account.

Verified-email auto-linking is enabled for Google and Apple. The provider must supply an email allauth marks verified, and the local address must also be verified and resolve to exactly one active user. Unverified, duplicate, or ambiguous matches are rejected; the adapter does not select an arbitrary user or erase an existing password. Emails are trimmed and lowercased when saved.

The Profile page lists linked providers. Disconnecting one requires the account password; social-only users must create a password first. A verified email or another linked provider must remain available before disconnecting the final provider. These checks are enforced by the application endpoint and allauth's own disconnect flow.

Set `SUPPORT_EMAIL` and `SUPPORT_PHONE` in the runtime environment to show real help contacts on the login and registration screen. Leave them unset until the correct public contact details are available.

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
http://127.0.0.1:8002/etaalthech2026/
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

Production keeps the server's existing Compose and host Nginx configuration. The Compose ports are backend `127.0.0.1:8002` and frontend `127.0.0.1:3002`; the host Nginx routes Admin/API/account paths to the backend and website paths to the frontend. Do not replace the server Compose or Nginx files during image deployment.

```bash
docker compose -f docker-compose.yml --env-file .env ps
```

Production keeps the existing host reverse proxy and Compose port mappings: Django is published at `127.0.0.1:8002`, and the frontend at `127.0.0.1:3002`. The host reverse proxy must send `/api/`, `/accounts/`, and the configured Django Admin path to port `8002`; normal website routes go to port `3002`. The deployment workflow does not replace the server's Compose or Nginx files.

On a successful push to `main`, CI tests the backend and frontend, runs browser tests, builds and publishes images, then deploys those exact commit-tagged images through a temporary Compose override. The server's existing Compose file, ports, Nginx configuration, and persistent volumes are left unchanged. The workflow only reports green after the live website, auth-options endpoint, and Django Admin login page pass smoke checks.

The support contact is `zoelewis.58@gmail.com`. Set `VITE_SUPPORT_EMAIL` in `eta_frontend/.env` for local frontend builds. Production frontend images read the same value from the GitHub Actions repository variable `VITE_SUPPORT_EMAIL`; if unset, the frontend config fallback uses this address.

## Local development notes

- The frontend runs in Vite on port 5174 for the local workstation setup.
- The backend runs Django on port 8002.
- PostgreSQL is the default development database for the project and is served through the Docker stack.
- Redis handles Celery messaging and background tasks through the same Docker environment.
- Celery worker and Celery beat run as part of the same Docker stack when needed.

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
5. Open `http://localhost:5174` and login.

If you need a token-based login for API access, use the `/api/auth/login/` endpoint with your username and password.

## Final note

This project is intentionally built to be container-first so you can evaluate it without installing Python, PostgreSQL, Redis, or Node directly on your machine.
