# Testing Guide

This guide explains how to run the automated tests for the HubbOps Platform.

## Prerequisites

You need a Python environment with `pip` installed.

## Backend Tests

The backend uses `pytest` for unit and integration testing.

### 1. Install Dependencies

Make sure you have the test dependencies installed:

```bash
cd backend
pip install -r requirements.txt
```

### 2. Run Tests

Run all tests:

```bash
pytest tests/
```

Run with verbose output:

```bash
pytest -v tests/
```

Run specific test file:

```bash
pytest tests/test_auth.py
```

### Test Coverage

-   **`tests/test_config.py`**: Verifies configuration loading, validation, and overrides.
-   **`tests/test_auth.py`**: Verifies user creation, authentication, password hashing, and permission logic.
-   **`tests/conftest.py`**: Provides test fixtures (in-memory SQLite database, async client).

## Frontend Tests

(Coming Soon)

## Continuous Integration

We recommend setting up a CI pipeline (e.g., GitHub Actions) to run these tests on every pull request.

Example `.github/workflows/test.yml`:

```yaml
name: Tests
on: [push, pull_request]
jobs:
  backend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
      - name: Run tests
        run: |
          cd backend
          pytest tests/
```
