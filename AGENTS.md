# Repository Guidelines

## Project Structure & Module Organization
- `python-project/app` contains the FastAPI application.
- `python-project/app/main.py` wires the app and includes routers.
- `python-project/app/routing` holds API route modules (health, users, tasks).
- `python-project/app/models` holds SQLAlchemy models and `Base`.
- `python-project/app/schemas` contains Pydantic request/response schemas.
- `python-project/app/services` and `python-project/app/repositories` isolate business logic and persistence.
- `docker-compose.yml` defines local services (API, Postgres, pgAdmin).

## Build, Test, and Development Commands
- `docker compose up --build` builds and starts API + database stack.
- `docker compose up` starts previously built images.
- `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000` runs the API locally if you install `python-project/requirements.txt`.

## Coding Style & Naming Conventions
- Python uses 4-space indentation and PEP 8 naming (`snake_case` for functions, `PascalCase` for classes).
- Keep routers thin; place validation in `schemas` and business logic in `services`.
- Keep model/table names consistent with existing SQLAlchemy models in `python-project/app/models`.
- Prefer explicit imports and keep module boundaries clear (`routing` → `services` → `repositories`).

## Testing Guidelines
- There is no dedicated test suite in the repository yet.
- When adding tests, create a `python-project/tests` package and name tests `test_*.py`.
- Keep tests close to behavior: API tests for routes, unit tests for services/repositories.

## Commit & Pull Request Guidelines
- Commit messages are short and imperative; optional prefixes like `feat:` appear in history.
  Example: `feat: Add project name to docker-compose.yml`.
- Include a clear PR description, list API changes, and link related issues.
- If you change API contracts or DB schema, call it out explicitly in the PR notes.

## Configuration & Security Tips
- Local configuration is loaded from `.env` via `docker-compose.yml`.
- Never commit secrets; prefer environment variables for DB credentials.
