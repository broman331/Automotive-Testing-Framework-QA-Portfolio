# subProj 9: XCP/CCP Calibration Automation Toolkit

## Description
This sub-project demonstrates automated parameter calibration and memory reading/writing using the **Universal Measurement and Calibration Protocol (XCP)**. 
XCP is an automotive standard used extensively in ECU development to tune algorithmic constants (like PID loops or generic calibration variables) in real-time without needing to recompile the C/C++ source code.

This toolkit features two main components:
1. **`xcp_ecu.py`**: A virtual ECU running a mock RAM map representing physical tuning variables (Speed Limits, AEB Gains, etc.).
2. **`xcp_master.py`**: A measurement/calibration script that automates XCP Command Receive Objects (CRO) to connect and overwrite the ECU's memory in real-time.

## Architecture

* **CONNECT (`0xFF`) / DISCONNECT (`0xFE`)**: Opens and closes the logical calibration session.
* **SET_MTA (`0xF6`)**: Sets the Memory Transfer Address (MTA) pointing to the specific hexadecimal memory block we intend to read or flash.
* **UPLOAD (`0xF5`)**: Queries the current payload stored at the MTA natively parsing the ECU's response (DTO).
* **DOWNLOAD (`0xF0`)**: Flashes bytes directly to the MTA.

## Test Coverage
The automated Pytest suite covers:
* **TC-901 XCP Connection Lifecycle**: Asserts session connections and ensures XCP commands are outright rejected with an `ERR_CMD_IGNORED` (`0x22`) if the connection is closed.
* **TC-902 Memory Upload**: Connects to the ECU and extracts the 4-byte payload mapping to the "Max Speed Limit" variable `0x1000`.
* **TC-903 Memory Download**: Automates a tuning scenario by overwriting the "AEB Braking Gain" parameter at `0x1004` and immediately validating the ECU registered the modification in its internal RAM structure.

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
