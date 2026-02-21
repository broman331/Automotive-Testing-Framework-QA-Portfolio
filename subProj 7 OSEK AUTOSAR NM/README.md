# subProj 7: OSEK/AUTOSAR NM State Machine Execution

## Overview
This sub-project demonstrates expert-level knowledge in automotive ECU power management, specifically focusing on the OSEK / AUTOSAR Network Management (NM) state machine. Properly coordinating sleep and wake cycles across dozens of nodes is critical in modern architectures to prevent 12V battery drain when the vehicle is turned off.

This pure-Python simulation constructs a virtual network ring and implements the strict 5-state AUTOSAR transition graph described by the specification: `Bus-Sleep` -> `Repeat-Message` -> `Normal-Operation` -> `Ready-Sleep` -> `Prepare-Bus-Sleep`.

## Architecture
* **`autosar_nm_node.py`**: The ECU class. Each instance maintains its own internal NM State timer variables (`timer_repeat_message`, `timer_nm_timeout`) and executes the transition boundaries based on local application requests (e.g., a door opening) and remote CAN bus PDU interrupts. It also extracts Partial Networking (PN) Identifiers and Control Bit Vectors (CBV) from the simulated payload.
* **`tests/test_nm_statemachine.py`**: The automated testing suite orchestrating `N=3` simulated ECUs. It passes mocked virtual CAN messages between them and strictly asserts that all three nodes synchronize their transitions to the millisecond.

## Test Coverage
The CI/CD pipeline validates eight specific transitional sequences:
1. **TC-701 Local Wakeup**: Verifies transition from `Bus-Sleep` to `Repeat-Message`.
2. **TC-702 Remote Wakeup Synchronisation**: Asserts that one node broadcasting a Wake command instantly pulls all sleeping nodes on the ring into the `Repeat-Message` state.
3. **TC-703 Steady State Maintenance**: Asserts that nodes requiring the bus cycle into `Normal-Operation` while nodes that don't transition into `Ready-Sleep` but stay online.
4. **TC-704 Ready Sleep Transition**: Asserts that a node finishing its network task correctly releases the bus and enters `Ready-Sleep`.
5. **TC-705 Prepare Bus Sleep Coordinated Shutdown**: Asserts the critical `t_NM_Wait` timeout where *all* nodes must be in `Ready-Sleep` together to transition to `Prepare-Bus-Sleep`.
6. **TC-706 Final Sleep Execution**: Evaluates the final safety timer before shutting down transceivers to reach `Bus-Sleep`.
7. **TC-707 CBV Active/Passive Wakeup Flags**: Asserts that waking ECUs properly flag whether they initiated the network wake, or were passively pulled awake by another ECU.
8. **TC-708 Partial Networking Isolation**: Asserts that waking messages carrying a specific PN Cluster ID are ignored by sleeping ECUs belonging to different logical clusters.

## Docker & Automation
Tests are fully containerized using Docker and executed automatically via the `.github/workflows/ci_subproj7.yml` pipeline.

### Running Locally
```bash
cd "subProj 7 OSEK AUTOSAR NM"
docker build -t subproj7 .
docker run --rm subproj7
```
