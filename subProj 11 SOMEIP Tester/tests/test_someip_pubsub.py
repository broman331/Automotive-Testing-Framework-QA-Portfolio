import pytest
import time
from someip_server import SomeipServer
from someip_client import SomeipClient

# Network Constants
HOST = "127.0.0.1"
SERVER_PORT = 30502 # Use distinct ports for pytest parallelism isolation
SD_PORT = 30491
SERVICE_ID = 0x1234
EVENTGROUP_ID = 0x0001
EVENT_ID = 0x8001

@pytest.fixture(scope="module")
def someip_server():
    server = SomeipServer(host=HOST, port=SERVER_PORT, sd_port=SD_PORT)
    server.start()
    time.sleep(0.5) # Give it time to bind and spin threads
    yield server
    server.stop()

@pytest.fixture(scope="module")
def someip_client():
    client = SomeipClient(host=HOST, sd_port=SD_PORT)
    yield client
    client.close()

def test_1101_detect_offered_service(someip_server, someip_client):
    """TC-1101: Client listens on the SD port and successfully detects the Service ID broadcast."""
    # The server is already broadcasting via the fixture.
    found = someip_client.wait_for_offer(SERVICE_ID)
    assert found is True, "Client failed to detect the SOME/IP OfferService broadcast."

def test_1102_eventgroup_subscription_lifecycle(someip_server, someip_client):
    """TC-1102: Client maps the SD structure into a SubscribeEventgroup struct, and asserts Server ACK."""
    # Send SubscribeEventgroup(0x1234, 0x0001) and await MSG_TYPE_RESPONSE (0x80)
    success = someip_client.subscribe_eventgroup(HOST, SERVER_PORT, SERVICE_ID, EVENTGROUP_ID)
    assert success is True, "Server rejected or failed to ACK the Eventgroup Subscription."
    
    # Assert server registered the client's app socket address
    assert len(someip_server.subscribers) == 1

def test_1103_decode_active_notification_payloads(someip_server, someip_client):
    """TC-1103: Assert Server cyclic broadcast correctly unpacks into Client struct float value."""
    # Since we are subscribed from the previous test, notifications should be arriving.
    # The baseline float is 45.1234, incrementing by 0.0001
    
    val1 = someip_client.receive_notification(SERVICE_ID, EVENT_ID)
    assert val1 is not None, "Failed to receive active notification mapping."
    assert 45.0 <= val1 <= 46.0, f"Payload unpacked incorrectly, got float {val1}"
    
    val2 = someip_client.receive_notification(SERVICE_ID, EVENT_ID)
    assert val2 is not None
    assert val2 > val1, "Server cyclic sequence failed to increment floating point correctly."

def test_1104_stop_subscribe_eventgroup_lifecycle(someip_server, someip_client):
    """TC-1104: Assert transmitting StopSubscribeEventgroup explicitly halts telemetry."""
    # Send StopSubscribeEventgroup(0x1234, 0x0001)
    success = someip_client.stop_subscribe_eventgroup(HOST, SERVER_PORT, SERVICE_ID, EVENTGROUP_ID)
    assert success is True, "Server failed to ACK the StopSubscribe event."
    
    # Assert server removed the client's app socket address
    assert len(someip_server.subscribers) == 0
    
    # Assert client no longer receives notifications
    val3 = someip_client.receive_notification(SERVICE_ID, EVENT_ID)
    assert val3 is None, "Client still receiving notifications after StopSubscribe."

def test_1105_malformed_header_rejection(someip_server, someip_client):
    """TC-1105: Assert that unsupported Protocol Versions are gracefully dropped."""
    # Ensure client is unsubscribed
    assert len(someip_server.subscribers) == 0
    
    # Transmit malformed Protocol Version 0x02
    someip_client.send_malformed_protocol(HOST, SERVER_PORT, SERVICE_ID, EVENTGROUP_ID, bad_version=0x02)
    
    # Give server time to process
    time.sleep(0.5)
    
    # Assert server rejected the payload and did not add the subscriber
    assert len(someip_server.subscribers) == 0, "Server incorrectly processed a subscription with a malformed Protocol Version."

