# How to Run MarketSafe

## Contents

- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
- [Run Locally](#run-locally)
- [Run in Production](#run-in-production)
- [Tests](#tests)
- [Lint](#lint)
- [Quick Reference](#quick-reference)

---

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) — required to run the full stack and integration tests
- [Node.js](https://nodejs.org/) v18+ — required to run frontend unit tests locally
- [Python](https://www.python.org/) 3.11+ — required to run backend unit and integration tests locally

---

## Environment Setup

Copy the example env file and fill in your values:

```bash
cp .env.example .env
```

The defaults in `.env.example` work out of the box for local development. At minimum, change the secret/password fields before deploying anywhere.

`SECRET_KEY` is used to sign JWT tokens. Generate a strong value with:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## Run Locally

Builds images from source and runs everything locally. Use this for development.

```bash
docker compose up --build
```

| Service  | URL                   |
| -------- | --------------------- |
| Frontend | http://localhost:4200 |
| Backend  | http://localhost:8000 |
| MinIO    | http://localhost:9001 |

To stop and remove containers:

```bash
docker compose down
```

To also remove persistent volumes (wipes the database):

```bash
docker compose down -v
```

---

## Run in Production

Pulls pre-built images from Docker Hub instead of building from source. Set `DOCKER_USERNAME=marketsafe` in your `.env` (this is the MarketSafe Docker Hub account).

```bash
docker compose -f docker-compose.prod.yml up
```

To stop:

```bash
docker compose -f docker-compose.prod.yml down
```

To also remove persistent volumes:

```bash
docker compose -f docker-compose.prod.yml down -v
```

> Make sure all secret values in `.env` (`SECRET_KEY`, passwords, etc.) are set to strong values before running in production.

---

## Tests

### Backend — Unit Tests

No Docker required. Run from the `server/` directory:

```bash
cd server
pip install -r requirements.txt
coverage run -m tests.unit.all_unit_tests
```

### Backend — Integration Tests

Requires Docker. The test suite automatically spins up a dedicated MySQL container on port **3307** (separate from the dev DB on 3306).

```bash
cd server
pip install -r requirements.txt
coverage run -m tests.integration.all_integration_tests
```

### Backend — All Tests (Unit + Integration)

```bash
cd server
pip install -r requirements.txt
coverage run -m tests.all_tests
```

### Backend — Coverage Report

```bash
cd server
coverage report -m
```

### Frontend — Unit Tests

```bash
cd frontend
npm test
```

This runs Karma/Jasmine tests in a headless Chrome browser and watches for file changes.

---

## Lint

### Frontend

```bash
cd frontend
npm run lint
```

---

## Quick Reference

| Task                      | Command                                                                                 |
| ------------------------- | --------------------------------------------------------------------------------------- |
| Start local stack         | `docker compose up --build`                                                             |
| Stop local stack          | `docker compose down`                                                                   |
| Start production stack    | `docker compose -f docker-compose.prod.yml up`                                          |
| Stop production stack     | `docker compose -f docker-compose.prod.yml down`                                        |
| Backend unit tests        | `cd server && pip install -r requirements.txt && coverage run -m tests.unit.all_unit_tests`                                |
| Backend integration tests | `cd server && pip install -r requirements.txt && coverage run -m tests.integration.all_integration_tests`                  |
| Backend all tests         | `cd server && pip install -r requirements.txt && coverage run -m tests.all_tests`                                          |
| Backend coverage          | `cd server && coverage report -m`                                                       |
| Frontend tests            | `cd frontend && npm test`                                                               |
| Frontend lint             | `cd frontend && npm run lint`                                                           |
