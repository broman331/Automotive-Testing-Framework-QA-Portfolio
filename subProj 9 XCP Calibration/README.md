# subProj 9: XCP/CCP Calibration Automation Toolkit

## Description
This sub-project demonstrates automated parameter calibration and memory reading/writing using the **Universal Measurement and Calibration Protocol (XCP)**. 
XCP is an automotive standard used extensively in ECU development to tune algorithmic constants (like PID loops or generic calibration variables) in real-time without needing to recompile the C/C++ source code.

This toolkit features two main components:
1. **`xcp_ecu.py`**: A virtual ECU running a mock RAM map representing physical tuning variables (Speed Limits, AEB Gains, etc.).
2. **`xcp_master.py`**: A measurement/calibration script that automates XCP Command Receive Objects (CRO) to connect and overwrite the ECU's memory in real-time.

## Architecture

* **CONNECT (`0xFF`) / DISCONNECT (`0xFE`)**: Opens and closes the logical calibration session.
* **GET_SEED (`0xF8`) / UNLOCK (`0xF7`)**: Security Access authentication enabling protected memory areas to be flashed.
* **SET_MTA (`0xF6`)**: Sets the Memory Transfer Address (MTA) pointing to the specific hexadecimal memory block we intend to read or flash.
* **UPLOAD (`0xF5`)**: Queries the current payload stored at the MTA natively parsing the ECU's response (DTO).
* **DOWNLOAD (`0xF0`)**: Flashes bytes directly to the MTA.
* **SHORT_UPLOAD (`0xF4`)**: An optimization querying MTA setup and data upload in a single 8-byte frame.

## Test Coverage
The automated Pytest suite covers:
* **TC-901 XCP Connection Lifecycle**: Asserts session connections and ensures XCP commands are outright rejected with an `ERR_CMD_IGNORED` (`0x22`) if the connection is closed.
* **TC-902 Protected Memory Access Denied**: Asserts that sending a `DOWNLOAD` to AEB parameters without cryptographic unlocking returns `ERR_ACCESS_DENIED` (`0x24`).
* **TC-903 Seed & Key Authentication**: Polls the ECU for a Seed, mathematically derives the Key, and successfully unlocks the internal state machine.
* **TC-904 Memory Upload**: Connects to the ECU and extracts the 4-byte payload mapping to the "Max Speed Limit" variable `0x1000`.
* **TC-905 Memory Download**: Automates a tuning scenario by authenticating and then overwriting the "AEB Braking Gain" parameter at `0x1004`.
* **TC-906 Short Upload**: Asserts structural decoding of the single-frame `SHORT_UPLOAD` mechanism.

## Docker & Automation
Tests are fully containerized using Docker and executed automatically via the `.github/workflows/ci_subproj9.yml` pipeline.

### Local Execution
To run the automated XCP read/write memory flash simulations locally:
```bash
cd "subProj 9 XCP Calibration"
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH=.
pytest tests/ -v
```
