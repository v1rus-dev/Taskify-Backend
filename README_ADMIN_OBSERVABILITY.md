# Taskify Admin + Observability

This project uses:

- `SQLAdmin` for standardized admin CRUD UI.
- `Grafana + Loki + Promtail` for centralized log history and filtering.

## Services and URLs

- SQLAdmin: `http://localhost:8082/admin`
- Grafana: `http://localhost:3000`
- Loki API (optional direct access): `http://localhost:3100`

## Start the stack

```bash
docker compose up --build
```

## Environment variables

Existing admin auth variables:

- `ENABLE_ADMIN=true`
- `ADMIN_BASIC_USER`
- `ADMIN_BASIC_PASSWORD`
- `ADMIN_TOKEN`

New/used logging variables:

- `LOG_LEVEL` (default: `INFO`)
- `LOG_JSON` (default: `true`)
- `LOG_FILE` (set per service in `docker-compose.yml`)
- `ADMIN_SESSION_SECRET` (recommended for SQLAdmin sessions)

Grafana variables:

- `GRAFANA_ADMIN_USER` (default: `admin`)
- `GRAFANA_ADMIN_PASSWORD` (default: `admin`)

## Log retention

Loki retention is configured to 30 days (`720h`) in:

- `observability/loki/loki-config.yaml`

## What is logged

Both API and admin services write JSON logs with these fields:

- `timestamp`
- `level`
- `logger`
- `message`
- `service`
- `request_id`
- `actor_id`
- `method`
- `path`
- `status_code`
- `duration_ms`
- `client_ip`
- `user_agent`

`actor_id` behavior:

- Valid Bearer JWT: `sub` claim value.
- Valid Basic admin auth: `admin:<username>`.
- Valid admin bearer token: `admin:token`.
- No valid auth: `anonymous`.

## Grafana Explore examples

In Grafana (`Explore`, datasource `Loki`), use queries like:

- All API logs:
  ```logql
  {job="taskify",service="api"}
  ```
- Requests by specific user:
  ```logql
  {job="taskify",actor_id="00000000-0000-0000-0000-000000000000"}
  ```
- Errors for tasks endpoints:
  ```logql
  {job="taskify",service="api"} | json | path=~"/tasks.*" | status_code >= 400
  ```
- Admin actions:
  ```logql
  {job="taskify",service="admin"} | json | actor_id=~"admin:.*"
  ```

## Notes

- Legacy custom admin endpoints (`/admin/logs/raw`, `/admin/logs/clear`, `/admin/db/*`) are no longer used.
- DB low-level inspection is still available via `pgAdmin` (`http://localhost:8083`).
