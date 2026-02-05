---
name: postman-api
description: Postman MCP workflow for FastAPI development and testing, find/get collections, run collections, create/update requests, manage mocks, and generate Python client code. Use when the user asks to test API endpoints, create/update Postman requests or mocks, or generate a Python client for an API.
---

# Postman API

## Overview

Use Postman MCP tools to inspect collections, run them for testing, and keep requests/mocks in sync with FastAPI endpoints. Generate Python client code from selected collections when asked.

## Quick Start

1. Resolve workspace context: if no workspace ID is provided, call getAuthenticatedUser, then getWorkspaces with createdBy to list workspaces and confirm the target.
2. Find the collection with getCollections (workspace + optional name filter).
3. Inspect details with getCollection (model=full if request details are needed).
4. Run tests with runCollection (include environmentId if variables are required).
5. Health check: run the `/health` request from the Taskify collection to confirm the server is up.

## Project Context

- Workspace: `My Workspace` (id `39e4d443-66b8-4b81-833a-8a8efb3bcb3f`)
- Collection: `Taskify` (uid `22311729-019f1198-36eb-44bc-a74a-b654a00f701e`)

## Core Tasks

### Find/Get Collections

- Use getCollections to list collections in a workspace.
- Use getCollection to retrieve full contents.
- Use getCollectionFolder/getCollectionRequest when only a specific item is needed.

### Create/Update Requests

- Create a request with createCollectionRequest (optionally folderId).
- Update name/method with updateCollectionRequest.
- For full request changes (URL, headers, body), fetch full collection, modify the request item, then putCollection with the updated payload.

### Manage Mocks

- List mocks with getMocks (prefer workspace scope).
- Create a mock with createMock (requires collection UID).
- Update mock settings with updateMock.
- Publish/unpublish with publishMock/unpublishMock.
- If only a collectionId is known, resolve UID via getCollection or construct from ownerId if needed.

### Generate Client Code (Python)

- Always call getCodeGenerationInstructions before any other Postman tool used for code generation.
- Default to Python sync client code (requests). If async is requested, use httpx.
- Follow the tool-provided flow for selecting the API/collection and generating code.

## Guardrails

- Ask for workspace ID if missing; confirm before using a fallback workspace.
- Avoid embedding secrets in collection variables.
- Keep Postman requests aligned with FastAPI routes (paths, methods, auth, payloads).
