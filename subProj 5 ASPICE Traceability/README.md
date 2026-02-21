# subProj 5: ASPICE Traceability & CI/CD Pipeline

## Overview
In the automotive industry, simply writing tests is not enough to achieve compliance with safety standards like **ISO 26262** or maturity models like **ASPICE**. 

Specifically, **ASPICE SWE.4 (Unit Verification)** and **SWE.6 (Software Qualification Testing)** require rigorous **traceability**. Every single test executed must cryptographically map back to a formalized Software Requirement Specification (SRS) ID. If a requirement exists but has no test proving its logic, the entire build must fail.

This project demonstrates how to build an automated ASPICE compliance pipeline using open-source tools (Python, Pytest, Docker, GitHub Actions) rather than expensive vendor-locked frameworks.

## Core Architecture
1. **Requirements Database (`requirements.json`)**: A mock database of software requirements (e.g., `REQ-001: Initialization`, `REQ-003: Safe State Degradation`).
2. **Pytest Integration (`test_mock_app.py`)**: A test suite that hooks custom `@pytest.mark.req("ID")` markers into natively exported `report.xml` JUnit XML files via a custom `conftest.py` interceptor.
3. **Traceability Engine (`traceability_generator.py`)**: A Python lexer that parses the simulated requirements alongside the Pytest execution log.
4. **Validation**: The engine maps `Requirement ID` -> `Test Case ID` -> `Execution Results`. It automatically generates a beautifully formatted Markdown Traceability matrix. If there is a missing test (0% coverage on a specific Requirement ID), it deliberately exits with `sys.exit(1)`, dropping the CI pipeline.

## Automation & CI/CD
This entire compliance check is wrapped in Docker and automated via GitHub Actions (`.github/workflows/ci_subproj5.yml`).
On every push, the cloud pipeline:
1. Builds the `aspice_pipeline` Docker abstraction.
2. Executes the test suite and runs the Traceability engine.
3. Fails the PR automatically if an engineer merges code that adds a requirement without a mapped test case.
4. Extracts and uploads the final `traceability_matrix.md` as an irrefutable artifact for compliance audits.

## Setup & Execution

### Local Build
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pytest test_mock_app.py --junitxml=report.xml
python traceability_generator.py
```

### Docker Verification
```bash
docker build -t aspice_pipeline .
docker run --rm aspice_pipeline
```
