# subProj 1: Virtual CAN Bus Framework

## Overview
This project simulates an Automotive Hardware-in-the-Loop (HiL) test environment. It uses `python-can` with a virtual interface to mock a vehicle network. A simulated ECU broadcasts "Vehicle Speed" and "Engine RPM" CAN messages, and a `pytest` suite validates the network timing, payload correctness, and system behavior during fault injection (like node dropout).

This project highlights expertise in ASPICE SWE.6 (Software Qualification Testing) and ISO 26262 functional safety validation.

## Running Locally

### Pre-requisites
- Python 3.10+

### Setup
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Run Tests
```bash
pytest
```
An HTML report will be generated at `report.html`.

## Docker Setup
To ensure environment parity and ease of CI/CD integration, a `Dockerfile` is provided.

```bash
docker build -t subproj1-can-tester .
docker run --rm -v $(pwd)/reports:/app/reports subproj1-can-tester
```

## Current Test Coverage
The `pytest` suite actively validates the following automotive system requirements:
- **Baseline Requirements**: Timing control (+/- 10ms jitter tolerance), payload packing (Speed/RPM), and missing node detection.
- **Robustness & Validation**:
  - **Babbling Idiot Node**: Simulates a defective ECU flooding the bus and asserts that the framework detects network saturation.
  - **Checksum Validations**: Verifies XOR checksum bytes are correctly calculated across data payloads.
  - **Out of Range Signals**: Asserts that the ECU ceiling/floors out-of-bounds metrics (Speed > 250km/h).
- **Network State Management (ASPICE SYS.4)**:
  - **Bus Sleep / Wakeup**: Asserts the ECU halts transmission on `0x600` Go-To-Sleep commands and resumes on Wakeup commands.
- **Reporting and Traceability**:
  - **Requirement Mapping**: Tests are decorated with custom `pytest` requirement markers (`@pytest.mark.req("REQ-001")`) to enable automated mapping to an ASPICE Requirement Traceability Matrix (RTM).

## Plan for Expanding the Test Suite
Moving forward, the test plan expands into the following advanced areas:

### 1. Complex Network Management
- **AUTOSAR Network Management (NM) Protocol**: Expand `MockECU` to handle standard OSEK/AUTOSAR NM messages, with tests verifying correct ring-state transitions and network synchronizations.

### 2. Physical Layer Defect Simulation
- **Corrupted Payloads**: Inject random bit-flips into the physical frame payload and verify that actual hardware-level CAN CRC validations reject the frames.
