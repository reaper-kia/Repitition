# Test suite

The suite is isolated from PostgreSQL, Redis, Kafka and Telegram. API tests use
FastAPI dependency overrides; application tests use in-memory fakes and mocks.

## Run everything

```bash
python -m pytest
```

## Run by layer

```bash
python -m pytest -m unit
python -m pytest -m api
python -m pytest -m e2e
```

## Structure

- `unit/` — domain objects, handlers, repository mappers, UoW, outbox,
  notifications, Kafka/Redis adapters and migration metadata.
- `api/` — request/response contracts, authorization boundaries and error
  mapping without a real database.
- `e2e/` — an in-memory scenario from catalog creation to preorder confirmation.

A failing test should be treated as a source-code regression or an unmet
contract, not fixed by weakening the assertion.
