# Contributing to MarketSafe

This document defines the workflow, coding standards, testing practices, and contribution expectations for all contributors.

All contributors are expected to read and follow this guide.

## Contents

- [0. Getting Started](#0-getting-started)
- [1. Branching Strategy](#1-branching-strategy)
- [2. Branch Naming Convention](#2-branch-naming-convention)
- [3. Coding Standards](#3-coding-standards)
- [4. Testing Standards](#4-testing-standards)
- [5. Code Coverage](#5-code-coverage)
- [6. Code Review](#6-code-review)
- [7. Usage of Generative AI](#7-usage-of-generative-ai)
- [8. Commit Message Convention](#8-commit-message-convention)
- [9. Pull Requests](#9-pull-requests)
- [10. CI/CD Pipeline](#10-cicd-pipeline)

---

## 0. Getting Started

1. Clone the repository
2. Follow [RUNNING.md](./RUNNING.md) to get the app running locally
3. Read through this guide before making any changes

### Architecture Overview

```
MarketSafe/
├── frontend/          # Angular app (TypeScript)
│   └── src/app/
│       ├── components/    # Shared UI components
│       ├── features/      # Page-level components
│       └── shared/        # Models, services, utilities
│
└── server/            # FastAPI backend (Python)
    └── src/
        ├── api/           # Routes and request/response converters
        ├── business_logic/
        │   ├── managers/  # Domain logic layer (validates + delegates to DB)
        │   └── services/  # Orchestration layer (used by routes)
        ├── db/            # Database access layer (MySQL implementations)
        ├── domain_models/ # Core domain objects
        └── utils/         # Shared validation, errors, helpers
```

Data flows top-down: `Route → Service → Manager → DB`, with domain models passed between layers.

| Layer          | Responsibility                                                              |
| -------------- | --------------------------------------------------------------------------- |
| Route          | Parses HTTP requests, calls the service, returns HTTP responses             |
| Service        | Orchestrates business operations across one or more managers                |
| Manager        | Validates inputs and delegates to the DB layer                              |
| DB             | Executes SQL queries and maps rows to domain models                         |
| Domain Models  | Plain data objects that carry state between layers — no business logic      |

`DB_MODE` in `.env` controls which seed scripts run on `db-init`: use `dev` for local development data and `prod` for a clean production schema.

---

## 1. Branching Strategy

```
[ feature branches ] → [ main ] → [ prod ]
```

- Create feature branches from `main`
- Pull from `main` daily before starting work
- Keep pull requests small and focused
- Any push to `main` should trigger a team notification
- `main` and `prod` are CI-protected

---

## 2. Branch Naming Convention

```
MSF-{ticket#}/short-description
```

Example:

```
MSF-231/add-login-endpoint
```

---

## 3. Coding Standards

### 3.1 Comments

- Add comments only where necessary
- Functions must include a header comment. Examples below:

#### Python (Docstring)

```python
def function_name(param1: type, param2: type) -> return_type:
    """
    Briefly describe what the function does.

    Args:
        param1 (type): Description of param1.
        param2 (type): Description of param2.

    Returns:
        return_type: Description of the returned value.
    """
```

#### TypeScript (JSDoc)

```ts
/**
 * Briefly describe what the function does.
 *
 * @param param1 Description of param1.
 * @param param2 Description of param2.
 * @returns Description of the returned value.
 */
function functionName(param1: Type, param2: Type): ReturnType {}
```

---

### 3.2 Naming Conventions

| Item             | Frontend (TypeScript) | Backend (Python)     |
| ---------------- | --------------------- | -------------------- |
| Folder Names     | example-folder-name   | example_folder_name  |
| File Names       | example-file-name.ts  | example_file_name.py |
| Classes / Enums  | ExampleClass          | ExampleClass         |
| Enum Values      | ALL_CAPS              | ALL_CAPS             |
| Functions        | exampleFunction()     | snake_case()         |
| Local Variables  | exampleVariable       | snake_case           |
| Global Variables | EXAMPLE_VARIABLE      | EXAMPLE_VARIABLE     |

---

### 3.3 Typing & Linting

- Specify types (both Angular and Python) for:
  - Variables
  - Parameters
  - Return values
- Use ESLint for frontend (Angular)
- Python functions visibility:
  - Protected: \_variable
  - Private: \_\_variable
- Use abstract classes as interfaces in Python

---

### 3.4 DRY Principle

- Do not repeat code
- If logic is reused, move it into a private/helper function
- Prefer many small functions over large functions

---

### 3.5 Python Constructors

- Use default parameter values where appropriate
- Always use explicit typing for constructor parameters
- Keep constructors simple and focused on initialization

#### Example

```python
class Client:
    def __init__(self, host: str, port: int = 443, timeout: float = 10.0):
        self.host = host
        self.port = port
        self.timeout = timeout
```

---

## 4. Testing Standards

### Structure

```
1. Arrange
2. Act
3. Assert
```

### Naming

TypeScript:

```
MethodName_StateUnderTest_ExpectedBehavior
```

Python:

```
test_MethodName_StateUnderTest_ExpectedBehavior
```

- Test files or classes must start with `test`
- Use Python unittest

### Execution

- Run unit and integration tests locally before opening a PR (see [RUNNING.md](./RUNNING.md))
- End-to-end (e2e) tests are manual — refer to the [Test Plan](./Test-Plan-MarketSafe.pdf) for test cases and procedures

---

## 5. Code Coverage

- Backend: 100% required
- Frontend: optional

---

## 6. Code Review

- Minimum of 1 reviewer
- Address all comments before merging

---

## 7. Usage of Generative AI

- Declare where Gen AI is used
- Do not blindly copy/paste
- Developer must understand and verify generated code

---

## 8. Commit Message Convention

| Prefix      | Usage                            |
| ----------- | -------------------------------- |
| FEATURE     | New feature                      |
| FIX         | Bug fix                          |
| REFACTOR    | Restructuring                    |
| IMPROVEMENT | Performance or logic improvement |
| UI          | UI changes                       |
| DOCS        | Documentation                    |
| TEST        | Tests                            |
| CONFIG      | Configuration                    |
| CHORE       | Cleanup                          |

Examples:

```
FEATURE: add password reset endpoint
FIX: resolve null pointer on empty listing response
REFACTOR: extract rating logic into RatingManager
TEST: add integration tests for offer service
CONFIG: update CORS allowed origins for prod
CHORE: remove unused import in account_routes
```

---

## 9. Pull Requests

- Use the provided PR template
- All checks must pass before merge
- Squash merge preferred unless otherwise stated

---

## 10. CI/CD Pipeline

The pipeline runs automatically on every push and pull request to `main` and `production`.

### CI (Continuous Integration)

Triggered on: push or pull request to `main` / `production`

**Frontend:**
1. Lint (`npm run lint`)
2. Unit tests (`ng test --watch=false --browsers=ChromeHeadless`)
3. Production build (`ng build --configuration=production`)

**Backend:**
1. Compile check (syntax validation across `src/`)
2. Unit tests with coverage (`coverage run -m tests.unit.all_unit_tests`)
3. Integration tests with coverage (`coverage run --append -m tests.integration.all_integration_tests`)
4. Coverage report uploaded as a downloadable HTML artifact on GitHub Actions

All CI checks must pass before a PR can be merged.

### CD (Continuous Delivery)

Triggered on: CI workflow completes successfully on `main` or `production`

Builds and pushes multi-platform Docker images (`linux/amd64`, `linux/arm64`) to the MarketSafe Docker Hub account:

| Image                          | Built from      |
| ------------------------------ | --------------- |
| `marketsafe/marketsafe-api`    | `./server`      |
| `marketsafe/marketsafe-frontend` | `./frontend`  |
| `marketsafe/marketsafe-db-init` | `./assets/db` |

These are the images pulled when running with `docker-compose.prod.yml`.

---
