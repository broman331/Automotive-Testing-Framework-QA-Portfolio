# subProj 2: Automated ADAS AEB SiL Tester

## Overview
This project constitutes a Software-in-the-Loop (SiL) testing framework for a mock Advanced Driver Assistance System (ADAS), specifically Autonomous Emergency Braking (AEB). 

The core AEB logic (calculating Time-To-Collision and issuing brake commands) is implemented in C++ (`aeb_logic.cpp`) to simulate production-level embedded code. A Python wrapper (`aeb_wrapper.py`) utilizing `ctypes` bridges the C++ memory space, allowing a robust, data-driven `pytest` suite to execute comprehensive boundary value and equivalence partitioning tests.

## Running Locally

### Pre-requisites
- GCC / G++ (to compile the shared library)
- Python 3.10+

### Setup
```bash
make  # Compiles aeb_logic.cpp into aeb_lib.so
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Run Tests
```bash
pytest
```
An HTML test report is generated as `report.html`.

## Docker Setup
The Docker setup ensures the C++ cross-compilation environment and the Python test harness remain synchronized across any test machine.

```bash
docker build -t subproj2-aeb-tester .
docker run --rm -v $(pwd)/reports:/app/reports subproj2-aeb-tester
```

## Current Test Coverage
The current suite utilizes a data-driven boundary value model mapped heavily against system thresholds (TTC < 1.0s and TTC < 2.5s).

Specifically, the suite validates:
- **Parameter Validation**: Tests strict boundary states spanning 10 unique matrix scenarios.
- **Signal Bouncing Hysteresis**: Validates C++ tracking over multiple cycles to assert phantom radar artifacts (1-tick blips) do not inadvertently lock the brakes up unnecessarily. 
- **Real-World Sensor Spoofing & Fuzzing**: Asserts the C++ architecture gracefully survives and handles injected `NaN`, `Infinity`, and wildly out-of-bounds metrics directly from the Python wrapper.
- **Monte Carlo Execution Latency**: Proves performance via thousands of complex floating-point operation simulations continuously guaranteeing execution remains below the 1ms native scheduling limit.
- **Structural/Grey-Box Testing (gcov)**: The Docker container executes `gcov` against the native C++ executions to output line-by-line branch coverage and MC/DC (Modified Condition/Decision Coverage) metrics, proving structurally complete tests.
- **Environmental Limits (Valgrind)**: The container wraps 3,000,000 randomized dynamic AEB braking evaluations inside the `Valgrind` diagnostic suite, proving the embedded C++ logic holds 0 memory leaks across long-running autonomous execution constraints.

## Plan for Expanding the Test Suite
Future QA expansion plans include:

### 1. Hardware-in-the-Loop (HiL)
- **Physical Sensor Injection**: Bridge the Python testing wrapper over a CAN/Ethernet hardware interface capable of feeding analog noise into a physical radar module to test true signal degradation.
