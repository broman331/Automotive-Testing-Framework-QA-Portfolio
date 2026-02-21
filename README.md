
<div align="center">
  <h1>🛡️ Automotive QA Portfolio</h1>
  <h3>Advanced Automotive Software Validation & Functional Safety (ASIL) Frameworks</h3>
  <p><i>A comprehensive engineering portfolio demonstrating modern Software-in-the-Loop (SiL) and Hardware-in-the-Loop (HiL) testing methodologies, network state management, and continuous integration tailored for safety-critical automotive domains.</i></p>
</div>

<hr />

## 🎯 To Hiring Managers & Recruiters
Welcome! This repository was specifically constructed to demonstrate advanced, hands-on proficiency in automotive testing methodologies critical to modern product roadmaps. 

While operating expensive proprietary tools like Vector CANoe and VectorCAST is a standard industry requirement, this portfolio aims to demonstrate something much deeper: **a fundamental, architectural understanding of what those tools actually do under the hood**.

By recreating Remaining Bus Simulation, ASPICE traceability matrices, Fuzzing algorithms, and ISO 26262 functional safety metrics entirely through **custom Python and C++ test harnesses**, this repository proves an ability to:
1. Engineer bespoke automated test solutions for any ECU network.
2. Assert strict structural coverage (`gcov`/`MC/DC`) and memory safety (`Valgrind`).
3. Maintain zero-compromise CI/CD pipelines compliant with automotive safety standards.

---

## 🚀 Project Hub: The 12 Automotive Testing Sub-Projects

Below is the roadmap of the 12 standalone automotive validation frameworks contained in this repository. 

> [!NOTE]
> **Each completed sub-project directory contains its own dedicated `README.md` file with deeper technical implementation details, setup instructions, and execution workflows.**

### ✅ Completed Projects

#### 1. Virtual CAN Bus Framework 
* **Domain:** CAN Network Simulation & Validation
* **What it does:** Recreates a Virtual CAN network mimicking a Hardware-in-the-Loop (HiL) setup. Features a multithreaded Mock ECU broadcasting Engine RPM/Speed signals over the `vcan` interface.
* **Testing Focus:** 
  * +/- 10ms real-time transmit jitter tolerance bounds.
  * Node disconnection handling and timeout timeouts.
  * Data payload XOR Checksum generation and validation.
  * Network Management (NM) State assertions (Go-To-Sleep `0x600` and Wakeup handling).
  * **Babbling Idiot Fuzzing**: Asserts correct failure detection when defective nodes saturate the bus with 1,000+ frames per second.
  * **ASPICE SYS.4 Traceability**: Direct logical linking between test functions (`@pytest.mark.req`) and system requirements for automated Traceability Matrices.

#### 2. Automated ADAS AEB SiL Tester 
* **Domain:** C++ Software-in-the-Loop (SiL) & Functional Safety 
* **What it does:** A lightweight, safety-critical Autonomous Emergency Braking (AEB) algorithm written in unmanaged C++, compiled to a shared library, and tested directly via Python `ctypes` wrappers. 
* **Testing Focus:**
  * Parameter Validation: Mathematical Time-To-Collision (TTC) boundary assertions across dynamic trajectory matrices.
  * **Signal Bouncing Hysteresis:** State-management tracking ensuring 1-tick radar artifacts (phantom braking data) do not lock up the braking system (simulating debounce filtering).
  * **ASIL-D Structural Coverage (`gcov`)**: CI/CD compilation flags asserting the C++ logic contains mathematical test coverage of all branches and decision trees.
  * **Embedded Memory Safety (`Valgrind`)**: 3,000,000 randomized continuous road tests validated by Valgrind resolving exactly 0 memory leaks across the execution loop.

#### 3. UDS (Unified Diagnostic Services) Protocol Fuzzer 
* **Domain:** ISO 14229 Diagnostics & Fuzzing
* **What it does:** Simulates a virtual ECU listening for ISO-TP formatted payloads utilizing `python-can` and `udsoncan`. Evaluates automated logic across key Unified Diagnostic Services handling standard responses and error states.
* **Testing Focus:**
  * Valid sequence flow assertions against critical Service Identifiers (SIDs): `0x10` (Session Control), `0x11` (Reset), `0x14` (Clear DTCs), `0x22` (Read Data By Identifier), `0x27` (Security Access), and `0x3E` (Tester Present).
  * **Negative Response Code (NRC) Fuzzing**: Artificially corrupting payload lengths (e.g., dropping bytes on `0x22`) or calling strictly secured SIDs out-of-order to assert the ECU correctly drops the frame and broadcasts the required ISO compliant fallback NRC (e.g., `0x13` Incorrect Length, `0x24` Request Sequence Error, `0x33` Security Access Denied).
  * **Dockerization & CI/CD Validation**: Implemented an automated GitHub Actions pipeline spinning up the virtual sub-framework and asserting negative response compliance logic perfectly across all targeted boundaries.

#### 4. CAPL-to-Python Converter
* **Domain:** Abstract Syntax Trees (AST) & Lexical Transpilation
* **What it does:** An automated build tool architected to ingest proprietary Vector CANoe `CAPL` scripts (`.can`) and logically decouple the logic into entirely open-source `python-can` code.
* **Testing Focus:** 
  * C-like Variable and Method extraction (`setTimer()`, `write()`, `output()`).
  * Converting CAPL's single-threaded event-blocks (`on start`, `on timer`, `on message`) into POSIX-compliant python daemon `Threads` and `can.Listener` Rx hooks.
  * **AST Error Handling**: Throwing explicit `ValueError` exceptions automatically when proprietary, non-translatable CAPL functions (like `testWaitForMessage`) are detected.
  * An automated `pytest` suite simulating live CAN execution against the generated Python strings.
  * **Dockerization & CI/CD Validation**: A GitHub Actions workflow builds a clean Docker abstraction testing the transpiler without polluting the host machine's Python packages.

#### 5. ASPICE Traceability & CI/CD Pipeline
* **Domain**: DevOps, Continuous Integration & Automotive Standards (SWE.4 / SWE.6)
* **What it does**: A pure Python Traceability Engine bridging an automated CI/CD Pytest lifecycle against a formalized Mock Requirement Database (JSON).
* **Testing Focus**:
  * **JUnit XML Parsing**: Built custom `conftest.py` hooks to inject `@pytest.mark.req("ID")` metadata natively into the generic `report.xml` output.
  * **ASPICE Coverage Logic**: The `traceability_generator.py` script maps `Requirement ID` -> `Test Case ID` -> `Execution Results`, forcing explicit traceability. It now intelligently handles 1-to-many, many-to-1, and orphans.
  * **One-to-Many Aggregation**: The generator aggregates multiple test conditions mapped to a single requirement identifier. If ANY child condition fails bounding checks, the parent requirement organically fails.
  * **Orphaned Test Detection**: The tool natively cross-references the XML logs against the formal JSON database, violently failing the pipeline if engineers define tests wrapped in unregistered specification markers.
  * **CI/CD Blockers**: An automated GitHub Actions pipeline builds the abstraction in Docker. The Traceability generator explicitly exits with code `1` and fails the pipeline if an engineer commits code that adds a requirement without linking a passing execution test case.

#### 6. HIL Mock Dashboard (PyQt5)
* **Domain**: GUI Development, Test Tooling, Python Automation.
* **What it does**: A `PyQt5` graphical dashboard visualizing a backend Vehicle Simulation engine displaying speed, RPM, and steering angle. Crucially provides simulated hardware fault-injection interfaces (sliders/buttons), and dynamic CSS-based safety warnings (e.g., turning speed readouts red at > 120km/h).
* **Testing Focus**:
  * **Headless UI Automation**: `pytest-qt` rigorously drives the GUI dynamically, sliding telemetry dials (Throttle, Steering) and clicking fault buttons (Brake Failure, Engine Overheat) autonomously.
  * **Xvfb Framebuffer CI Integration**: The GitHub Actions pipeline installs `Xvfb` (X virtual framebuffer) onto Ubuntu headless runners allowing Qt to draw visually "in-memory" and fully automating robust `pytest-qt` visual validation.

---

#### 7. OSEK/AUTOSAR NM State Machine Execution
* **Domain**: Software Standards, Power Management, State Machine Testing.
* **What it does**: Implements the strict 5-state AUTOSAR/OSEK Network Management protocol (`Bus-Sleep` -> `Repeat-Message` -> `Normal-Operation` -> `Ready-Sleep` -> `Prepare-Bus-Sleep`). Simulates a virtual multi-node ring over CAN to demonstrate how ECUs collaboratively decide to sleep (saving the 12V battery) or wake up synchronously.
* **Testing Focus**:
  * **Network Synchronization**: `pytest` asserts that broadcasting a keep-alive from one node correctly pulls all other sleeping nodes into the `Repeat-Message` state.
  * **Coordinated Shutdown**: Automated timing tests ensuring the global transition to `Prepare-Bus-Sleep` only occurs when *all* simulated nodes fall silent.
  * **Partial Networking & CBV Parsing**: Tests validate that waking payloads carrying specific Partial Networking Identifiers successfully wake up their target clusters while leaving isolated ECUs in deep sleep, and correctly parse Active/Passive wakeup flags from the Control Bit Vector.

---

#### 8. ISO 26262 Fault Injection Framework (Failure Modes)
* **Domain**: Functional Safety, ISO 26262 Hardware Fault Modeling & AUTOSAR E2E Profiles.
* **What it does**: Simulates critical physical failures on the CAN bus using a Man-In-The-Middle (MITM) python proxy. Specifically injects: `DROP_ALL` (cut wires), `LATENCY` (CPU starvation), `CORRUPT_PAYLOAD` (Bit-flipping EMI), `STALE_DATA` (frozen ADC sensors), `CORRUPT_CRC` (E2E cryptographic corruption), and `DUPLICATE_FRAME` (Gateway replay loops).
* **Testing Focus**:
  * **Safe State Evaluation**: Automated Pytest execution asserting that the target ECU correctly identifies the injected mathematical anomalies and safely degrades into predetermined `SafeState` enum modes (e.g. `TIMING_VIOLATION`, `IMPLAUSIBLE_SIGNAL`) rather than catastrophically failing.
  * **AUTOSAR End-to-End (E2E) Profile 1 Validation**: 
    * Sabotages CRC algorithm derivations mid-flight, verifying the payload drops and triggers an `E2E_CRC_ERROR`.
    * Duplicates messages synchronously to mimic replay attacks, validating sequence counter protection blocks the data array and asserts an `E2E_SEQ_DUPLICATION`.

---

#### 9. XCP/CCP Calibration Automation Toolkit
* **Domain**: Measurement and Calibration Protocols (XCP), Parameter Tuning.
* **What it does**: Automates an XCP Master connecting to a Mock Slave ECU holding a virtual internal memory map. Uses standard XCP formatted payloads (e.g. `0xFF` Connect, `0xF8` Get_Seed, `0xF6` Set_MTA, `0xF4` Short_Upload, `0xF0` Download).
* **Testing Focus**:
  * **Session Validation**: Asserts that memory transfer commands are securely rejected (`ERR_CMD_IGNORED`) if the tool has not initiated a formal `CONNECT` sequence.
  * **Security Access (Seed & Key)**: Proves ECU security by artificially denying write access (`ERR_ACCESS_DENIED`) to critical addresses unless the master dynamically requests a Seed and accurately calculates the correct cryptographic Key to `UNLOCK` the session.
  * **Memory Polling (Read)**: `pytest` automatically sweeps specified hex addresses (e.g. `0x1000` Max Speed Limit) via `SHORT_UPLOAD`, successfully deciphering little-endian ECU DTO responses back into python integers.
  * **On-The-Fly Flashing (Write)**: Tests dynamically tuning AEB Braking Gain parameters by constructing `DOWNLOAD` payloads and forcefully mutating the internal memory dictionary of the targeted Slave, verifying the write logic holds.

---

#### 10. VectorCAST Log Parser (CI/CD Dashboard Integration)
* **Domain**: Test Metric Aggregation, CI/CD Scripting.
* **What it does**: A lightweight Python engine utilizing `xml.etree.ElementTree` to ingest enterprise test reports (VectorCAST execution and structural coverage `.xml` payloads) generated by Jenkins or GitHub Actions. It elegantly aggregates massive log directories into a singular `.json` file representing total organizational pass rates and coverage math.
* **Testing Focus**:
  * **Execution Consolidation**: Asserts that `passed`, `failed`, and `total` counters successfully sum dynamically across disjointed suite payloads.
  * **Coverage Fractional Averaging**: Validates the mathematical precision when calculating `Statement Coverage`, `Branch Coverage`, and `MC/DC Coverage` across separate C/C++ target files simultaneously.
  * **Malformed Yield Resilience**: Proves the CI job doesn't fundamentally crash if passed a corrupted or incomplete XML log. The script natively throws and logs `ET.ParseError` exceptions while successfully continuing to parse the remaining valid nodes.

---

### 🚧 Future Pipeline (Sub-Projects 11-12)

#### 11. Automotive Ethernet (SOME/IP) Protocol Tester
* **Focus**: Modern Infotainment/Zonal Architectures
* **What it will do**: Send structured SOME/IP (Scalable service-Oriented MiddlewarE over IP) payloads over UDP.
* **Testing**: Assert dynamic Service Discovery (SD) and Publish/Subscribe pattern event listeners over a mock high-speed automotive network.

#### 10. IVI (In-Vehicle Infotainment) E2E UI Automation
* **Focus**: Frontend UI / Appium
* **What it will do**: Use Appium/Selenium framework patterns adapted for automotive touch displays.
* **Testing**: Automated layout detection, touch boundary testing, and assertion of visual layout elements for Qt/Android Automotive infotainment screens.

#### 11. OTA (Over-The-Air) Delta Payload Validator
* **Focus**: Device Management & Telemetry
* **What it will do**: Simulate fetching compressed differential software updates from a cloud server down to an edge ECU.
* **Testing**: Assert the cryptographic signature validation of the mock binary blob, ensuring the module rejects unsigned/corrupted firmware downloads.

#### 12. ASPICE Traceability Dashboard
* **Focus**: Process Improvement (V-Model) 
* **What it will do**: A lightweight React/Vite dashboard connecting to a mock Jira/Requirement database.
* **Testing**: Parses the `pytest` output XML/JSON metadata gathered from all 11 previous subprojects to map executed code tests directly to written user requirements, outputting a fully conformant Requirement Traceability Matrix (RTM).
