# subProj 11: Automotive Ethernet SOME/IP Protocol Tester

## Description
In modern automotive architectures (like Zonal architectures or complex Infotainment units), traditional CAN buses lack the bandwidth and payload depth required for high-speed sensor streams. **SOME/IP** (Scalable service-Oriented MiddlewarE over IP) handles these complex Service-Oriented architectures over Automotive Ethernet (UDP/TCP).

This sub-project implements a Mock SOME/IP network simulator utilizing Python `socket` clusters to demonstrate:
1. **Service Discovery (SD)** broadcasting.
2. **Publish/Subscribe (PubSub)** eventgroup architectures, including `StopSubscribe` lifecycle management.
3. High-speed `Notification` cyclic telemetry parsing.
4. **Protocol Handshaking** dropping explicitly malformed data structures.

## Architecture

* **`someip_server.py`**: A mocked Zonal ECU. It boots isolated threading loops allowing it to actively broadcast `OfferService` SD structures over UDP to alert local nodes of its presence. It natively parses incoming subscriptions, stores active client addressing, and cyclically dumps mathematical coordinates (simulating GPS/Camera bounding boxes) as 32-bit floating-point geometries. It handles teardown sequences properly.
* **`someip_client.py`**: The Client/Tester application. It actively monitors SD multicast IP channels, intercepts the ECU Service IDs, formally transmits a `SubscribeEventgroup` socket payload, and ultimately consumes and mathematically unpacks the floating point data streams back into Python native assertions. It can also intentionally spoof unsupported Protocol Versions to test network resilience.
* **`tests/test_someip_pubsub.py`**: The Pytest orchestration asserting timeline lifecycle events accurately traverse the UDP infrastructure.

## Test Coverage
* **TC-1101 Detect Offered Service**: Validates the Python client actively intercepts the `OfferService` sequence asynchronously emitted by the target Server.
* **TC-1102 Eventgroup Subscription Lifecycle**: Asserts that transmitting the formal 16-byte `SubscribeEventgroup` request successfully transitions the native server's internal memory struct, eliciting a `SubscribeEventgroupAck` response array.
* **TC-1103 Decode Active Notification Payloads**: Proves that the subscribed mock GPS cyclic byte streams structurally cast back into accurate 32-bit `float` python coordinates exactly matching the server timeline.
* **TC-1104 StopSubscribeEventgroup Lifecycle**: Asserts that transmitting a formal `StopSubscribeEventgroup` header cleans up the server's subscription arrays and explicitly halts all incoming telemetry for that client socket.
* **TC-1105 Malformed Header Rejection**: Asserts that transmitting a subscription or generic payload utilizing an unsupported Protocol Version (e.g. `v2` instead of `v1`) forces the server to gracefully drop the packet without crashing the async listener loop.

## Docker & Automation
Tests are fully containerized using Docker and executed automatically via the `.github/workflows/ci_subproj11.yml` pipeline.

### Local Execution
To run the framework locally:
```bash
cd "subProj 11 SOMEIP Tester"
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH=.
pytest tests/ -v
```
