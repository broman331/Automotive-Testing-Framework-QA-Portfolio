
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

---

### 🚧 Future Pipeline (Sub-Projects 3-12)

#### 3. UDS (Unified Diagnostic Services) Protocol Fuzzer
* **Focus**: ISO 14229 Diagnostics
* **What it will do**: Implement an automation layer that transmits UDS SID arrays (e.g., `0x10` Diagnostic Session Control, `0x22` Read Data By Identifier) over Virtual CAN.
* **Testing**: Assert that negative response codes (NRCs) are correctly returned on invalid payload lengths or improperly authenticated security access (`0x27`).

#### 4. CAPL Scripting Equivalency Node (Remaining Bus Simulation)
* **Focus**: Network Topologies
* **What it will do**: Provide an open-source, Python-based equivalent to Vector's CAPL language.
* **Testing**: Load `.dbc` (CAN database) files and automatically parse network topologies to spin up mock ECUs simulating the "rest of the bus" around a System Under Test (SUT).

#### 5. CI/CD Automotive Validation Pipeline
* **Focus**: DevOps & Continuous Integration
* **What it will do**: A complex GitHub Actions matrix that spins up virtual CAN environments inside Docker containers.
* **Testing**: Asserts pipeline failures on branch code coverage drops below 100%, generates auto-updating HTML Test Reports (from subProj 1/2), and builds automated Docker images of the test suites.

#### 6. OSEK/AUTOSAR NM State Machine Execution
* **Focus**: AUTOSAR Network Management
* **What it will do**: Expand the basic Sleep/Wake commands of SubProj 1 into a full AUTOSAR logical ring topology.
* **Testing**: Validating transition state graphs (Bus-Sleep -> Prepare-Bus-Sleep -> Network-Mode -> Repeat) ensuring nodes don't drop off the logical ring synchronously.

#### 7. ISO 26262 Fault Injection Framework (Failure Modes)
* **Focus**: Hardware Fault Defect Simulation
* **What it will do**: Simulate dropped bits, inverted frames, and extreme processor latencies.
* **Testing**: Automatically evaluate if the Software-Under-Test gracefully enters a pre-defined "Safe State" or triggers standard Diagnostic Trouble Codes (DTCs).

#### 8. XCP/CCP Calibration Automation Toolkit
* **Focus**: Measurement and Calibration
* **What it will do**: A script module simulating XCP/CCP DAQ (Data Acquisition) lists over Ethernet or CAN.
* **Testing**: Verifying that internal microcontroller memory address sweeps can be effectively spoofed and measured by the automated tooling.

#### 9. Automotive Ethernet (SOME/IP) Protocol Tester
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
