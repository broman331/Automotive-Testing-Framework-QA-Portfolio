# subProj 8: ISO 26262 Fault Injection Framework (Failure Modes)

## Overview
This sub-project demonstrates safety-critical test engineering aligned with **ISO 26262 Functional Safety** standards. Modern vehicles must not crash or behave erratically when physical hardware fails (e.g., a cut wire, EMI corruption, or a frozen sensor ADC). Instead, they must gracefully detect the anomaly and transition into a predetermined Safe State.

This repository features a Man-In-The-Middle (MITM) CAN logic proxy simulating physical defects, alongside a target ECU actively trying to mitigate them.

## Architecture
1. **`fault_proxy.py`**: A synthetic router placed between the sensor outputs and the target ECU inputs. It can dynamically inject hardware failures into the data stream:
    * `DROP_ALL`: Simulates total connectivity loss.
    * `LATENCY`: Simulates critical CPU starvation or network congestion.
    * `CORRUPT_PAYLOAD`: Simulates Electromagnetic Interference (EMI) flipping significant payload bits.
    * `STALE_DATA`: Simulates a sensor locking up and transmitting frozen data sequences.
    * `CORRUPT_CRC`: Tests AUTOSAR E2E Profile 1 by sabotaging cryptographic payload checksums.
    * `DUPLICATE_FRAME`: Replicates sequence counters to mimic gateway loops or Malicious Replay Attacks.
2. **`safety_ecu.py`**: The Software-under-Test tracking incoming messages. It parses Delta-V physics constraints, cycle timers, and sequence numbers.
3. **`tests/test_iso26262_faults.py`**: The `pytest` test suite controlling the Proxy faults and asserting that the ECU transitions to the correct Safe State (e.g., `IMPLAUSIBLE_SIGNAL`, `TIMING_VIOLATION`, `SAFE_STATE_COM_LOSS`).

## Test Coverage
The automated Pytest suite covers:
* **TC-801 Total Signal Loss**: Validates the 50ms absolute timeout limit.
* **TC-802 High Latency**: Validates jitter calculation. If a message is delayed but the timeout limit hasn't tripped, it is correctly flagged as a timing violation rather than complete loss.
* **TC-803 EMI Bit-Flipping**: Validates mathematical integrity. If the payload dictates an impossible 129km/h speed jump in 20 milliseconds, the ECU rejects it.
* **TC-804 Stale Data Lock**: Validates sequence parsing. If the payload is identical for 3 consecutive sequences, the stream is flagged as frozen.
* **TC-805 E2E CRC Checksum**: Validates the payload-to-hash match. The module protects against dirty payloads bypassing checksum gates.
* **TC-806 E2E Sequence Duplication**: Counters message saturation or Replay spoofing by isolating consecutive matching Sequence IDs.

## Docker & Automation
Tests are fully containerized using Docker and executed automatically via the `.github/workflows/ci_subproj8.yml` pipeline.

### Running Locally
```bash
cd "subProj 8 ISO26262 Fault Injection"
docker build -t subproj8 .
docker run --rm subproj8
```
