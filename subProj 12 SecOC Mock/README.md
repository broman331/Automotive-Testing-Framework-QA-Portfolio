# subProj 12: Secure Onboard Communication (SecOC) Mock

## Description
Traditional CAN networks are broadcast-based and explicitly lack encryption or message authentication, rendering them vulnerable to spoofing, Man-In-The-Middle (MITM), and Replay attacks. 

AUTOSAR SecOC mitigates these vulnerabilities by appending a cryptographic Message Authentication Code (MAC) to critical payloads. This MAC is derived from a complex hashing algorithm (e.g., AES-CMAC) combining the base Data Payload with a synchronized, monotonically incrementing **Freshness Value (FV)**. 

This sub-project simulates a SecOC environment over a mock python infrastructure.

## Architecture

* **`secoc_crypto.py`**: A python library simulating the core AES-CMAC logic (via `hashlib`/`hmac`). It mathematically hashes the target payload alongside an internal monotonic counter (FV), explicitly asserting algorithms to trap and reject stale freshness values or manipulated byte arrays.
* **`secoc_nodes.py`**: Simulates the endpoints of a CAN network:
  * `TransmitterECU`: Generates the MAC, synchronizes the FV, and constructs the secure dictionary simulating a SecOC-compliant CAN payload.
  * `ReceiverECU`: Intercepts the dictionary, runs a strictly independent cryptographic hash leveraging its own parallel FV logic, and enforces drop-rules on mismatch.
* **`tests/test_secoc.py`**: The fully automated Pytest architecture deliberately attacking the Receiver ECU to prove cyber resilience.

## Test Coverage
* **TC-1201 Valid MAC Acceptance**: Mocks a synchronized environment, asserting that an untouched, perfectly constructed MAC payload successfully evaluates natively.
* **TC-1202 Invalid MAC Rejection**: Mimics a Man-In-The-Middle attacker intercepting a valid frame, modifying the internal Data Byte (e.g. accelerating a vehicle), and passing it dynamically to the Receiver. The backend correctly raises a `MacValidationError` discovering the underlying data payload no longer mathematically yields the transmitted MAC.
* **TC-1203 Stale Freshness Value Rejection**: Simulates a hacker recording a perfectly valid and mathematically true legacy CAN frame, attempting to re-inject it onto the bus milliseconds later. The Receiver explicitly detects the older Freshness Value and drops the package, throwing a `ReplayAttackError`.

## Docker & Automation
Tests are fully containerized using Docker and executed automatically via the `.github/workflows/ci_subproj12.yml` pipeline.

### Local Execution
To run the framework locally:
```bash
cd "subProj 12 SecOC Mock"
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH=.
pytest tests/ -v
```
