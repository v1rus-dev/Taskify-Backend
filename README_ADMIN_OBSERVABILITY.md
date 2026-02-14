# Taskify Admin

The project uses SQLAdmin for the admin CRUD UI.

## Services and URLs

Вход только через nginx (два порта):

- **Порт 80** — приложение (API). Пример: `http://localhost/` или `http://your-server/`
- **Порт 8080** — всё админское: SQLAdmin по корню `/`, pgAdmin по `/pgadmin/`. Примеры: `http://localhost:8080/`, `http://localhost:8080/pgadmin/`

## Start the stack

```bash
docker compose up --build
```

## Environment variables

Admin auth:

- `ENABLE_ADMIN=true`
- `ADMIN_BASIC_USER`
- `ADMIN_BASIC_PASSWORD`
- `ADMIN_TOKEN`

Logging:

- `LOG_LEVEL` (default: `INFO`)
- `LOG_JSON` (default: `true`)
- `LOG_FILE` (set per service in `docker-compose.yml`)
- `ADMIN_SESSION_SECRET` (recommended for SQLAdmin sessions)

## SQLAdmin features

- **Logs (custom):** menu item "Logs" under System — live tail of server log (Admin or API), pause/resume, clear list. Requires same auth as admin.
- **Tasks:** create/edit with user and tags in one form; list shows title, owner (user), completed, dates; filter by completed and user; search by title; export CSV/JSON.
- **Users:** list/search by email, name, friend tag; password is not editable from admin; export CSV/JSON.
- **SubTasks, Tags, Friend requests, Sync events/ops:** list, search, filters, sort, export where applicable.
- **Menu:** grouped by Users, Tasks, Friends, Sync.

## Logs

API and admin write JSON logs. View with:

```bash
docker compose logs -f api
docker compose logs -f admin
```
