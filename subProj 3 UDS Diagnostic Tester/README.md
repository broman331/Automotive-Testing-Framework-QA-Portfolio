# subProj 3: UDS (Unified Diagnostic Services) Protocol Fuzzer

## Overview
This project demonstrates an automated ISO 14229 UDS (Unified Diagnostic Services) testing harness. It utilizes a custom Python-based Mock ECU (`uds_ecu.py`) connected to a virtual CAN interface (`vcan`). The ECU is capable of deciphering incoming ISO-TP payloads and logically managing Diagnostic Sessions, Security Access states, and Data Identifiers (DIDs).

The testing suite (`test_uds.py`) leverages the `udsoncan` library to automate UDS requests and mathematically assert both standard execution and out-of-bounds **Fuzzing**.

## Testing Scope
This project specifically simulates and validates the following critical UDS SIDs (Service Identifiers) using `pytest`:

1. **`0x10` Diagnostic Session Control**: Validates state management and rejects unsupported subfunctions with NRC `0x12`.
2. **`0x22` Read Data By Identifier**: Successfully parses and retrieves the 17-byte VIN at `0xF190`. Fuzzing this SID with truncated payloads successfully triggers NRC `0x13` (Incorrect Message Length), and restricted addresses safely trigger NRC `0x31` (Out of Range).
3. **`0x27` Security Access**: Implements a full challenge/response Seed & Key cryptographic algorithm. The ECU accurately restricts execution with NRC `0x24` (Sequence Error) if the Tester attempts to send a Key without a Seed, and NRC `0x33` (Denied) on an invalid Key formulation.

## Setup & Execution

1. Build the local virtual environment and install dependencies:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Run the entirely self-contained test suite and HTML RTM reporter:
```bash
pytest test_uds.py --html=report.html --self-contained-html
```
