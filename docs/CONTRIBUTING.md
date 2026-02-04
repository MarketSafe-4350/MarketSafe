# Contributing to MarketSafe

This document defines the workflow, coding standards, testing practices, and contribution expectations for all contributors.

All contributors are expected to read and follow this guide.

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
MSF-{ticket#}:short-description
```

Example:

```
MSF-231:add-login-endpoint
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

- Run unit, integration, and e2e tests locally before opening a PR

---

## 5. Code Coverage

- Backend: 100% required
- Frontend: optional

---

## 6. Code Review

- Minimum of 2 reviewers
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

Example:

```
FEATURE: add password reset endpoint
```

---

## 9. Pull Requests

- Use the provided PR template
- All checks must pass before merge
- Squash merge preferred unless otherwise stated

---
