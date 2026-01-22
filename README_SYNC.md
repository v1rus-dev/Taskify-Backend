# Sync (Offline-First) Overview

This document explains the offline-first sync approach implemented on the server for Taskify.
It is intended for the mobile client team.

## Goals
- Offline-friendly creates/updates/deletes
- No payload stored in the sync log
- Safe idempotent push from client
- Simple pull with cursor

## Key Concepts

### 1) Client IDs (`client_id`)
The client generates UUIDs for records created offline.
Server stores `client_id` in core tables to map offline records to server IDs.

Tables:
- `tasks.client_id`
- `subtasks.client_id`
- `tags.client_id`

Mapping is returned by the server during push.

### 2) Sync Events (Server Log)
The server logs *what changed* in a compact event table.
No payload is stored. On pull, server reads fresh data from the DB.

Table: `sync_events`
- `id` (cursor)
- `user_id`
- `entity` (`task` | `subtask` | `tag`)
- `entity_id`
- `op` (`create` | `update` | `delete`)
- `occurred_at`

### 3) Sync Ops (Idempotency)
Client sends operations with `op_id`.
Server stores `op_id` per user to deduplicate.

Table: `sync_ops`
- `user_id`
- `op_id`
- `device_id` (optional)
- `created_at`

## API Endpoints

### Pull changes
`GET /sync/changes?cursor=0&limit=200&compact=true`

- `cursor` — last seen event id (start at 0)
- `limit` — max events per page
- `compact=true` — return only last event per entity within the page

Response:
```json
{
  "next_cursor": 123,
  "changes": [
    {
      "id": 120,
      "entity": "task",
      "entity_id": 10,
      "op": "update",
      "occurred_at": "2026-01-22T12:00:00Z",
      "data": {
        "id": 10,
        "title": "...",
        "deleted_at": null,
        "client_id": "..."
      }
    },
    {
      "id": 121,
      "entity": "subtask",
      "entity_id": 55,
      "op": "delete",
      "occurred_at": "2026-01-22T12:01:00Z",
      "data": {
        "id": 55,
        "deleted_at": "2026-01-22T12:01:00Z"
      }
    }
  ]
}
```

Notes:
- `data` is fetched live from the DB.
- For soft-deleted records, `deleted_at` is set.
- If a record is hard-deleted and not found, `data` may be `null` (currently tasks/subtasks/tags are soft-deleted).

### Push changes
`POST /sync/push`

Request:
```json
{
  "device_id": "uuid",
  "ops": [
    {
      "op_id": "uuid",
      "entity": "task",
      "op": "create",
      "client_id": "uuid",
      "data": { "title": "Test", "description": "...", "is_completed": false }
    },
    {
      "op_id": "uuid",
      "entity": "subtask",
      "op": "create",
      "client_id": "uuid",
      "data": { "task_client_id": "uuid", "text": "Call", "is_completed": false }
    }
  ]
}
```

Response:
```json
{
  "ack": ["op_id_1", "op_id_2"],
  "id_map": {
    "task": [{"client_id": "uuid", "id": 101}],
    "subtask": [{"client_id": "uuid", "id": 501}],
    "tag": []
  },
  "errors": []
}
```

Notes:
- `op_id` ensures idempotency.
- If the same `op_id` is sent again, server returns `ack` without reapplying.
- `client_id` is mapped to server IDs in `id_map`.

## Client Flow (Recommended)

1) Offline create
- Generate `client_id`
- Save to local DB
- Add op to queue

2) Push
- Send queued ops to `/sync/push`
- Apply `id_map` to replace `client_id` with real `id`

3) Pull
- Call `/sync/changes?cursor=...&compact=true`
- Apply changes in order
- Store `next_cursor`

## Entities & Operations

Supported entities: `task`, `subtask`, `tag`

Supported ops: `create`, `update`, `delete`

### Subtask create using task_client_id
If a task was created offline and not yet mapped, use `task_client_id` in subtask `data`.
Server resolves task via `client_id`.

## Soft Delete
Tasks, subtasks, tags use `deleted_at`.
- Delete requests set `deleted_at`.
- Sync changes include `deleted_at` in `data`.

## Known Limitations / Next Steps
- Task↔tag relations are not pushed via `/sync/push` yet.
  Use existing task update APIs or extend push to include `tag_client_ids`.
- No conflict resolution beyond last-write-wins (LWW).
- `compact=true` only collapses within the current page.

## DB Fields Reference (Sync)

### tasks
- `id`, `client_id`, `deleted_at`, `updated_at`

### subtasks
- `id`, `client_id`, `deleted_at`, `updated_at`

### tags
- `id`, `client_id`, `deleted_at`, `updated_at`

### sync_events
- `id`, `user_id`, `entity`, `entity_id`, `op`, `occurred_at`

### sync_ops
- `id`, `user_id`, `op_id`, `device_id`, `created_at`
