import pytest
from secoc_crypto import MacValidationError, ReplayAttackError
from secoc_nodes import TransmitterECU, ReceiverECU

# Common Shared Secret Key across perfectly synchronized ECUs
SHARED_SECRET = b"1234567890123456" # 16 bytes for AES-128 simulation

@pytest.fixture
def test_network():
    """Initializes a synchronized Transmitter and Receiver ECU pair."""
    tx = TransmitterECU(SHARED_SECRET)
    rx = ReceiverECU(SHARED_SECRET)
    return tx, rx

def test_1201_valid_mac_acceptance(test_network):
    """TC-1201: Assert properly secured payload passes MAC validation."""
    tx, rx = test_network
    
    # 8-byte CAN payload (e.g. Steering Angle Request)
    payload = b"\x01\x02\x03\x04\x05\x06\x07\x0A"
    msg_id = 0x100
    
    # TX constructs the secure dict
    secure_frame = tx.secure_transmit(message_id=msg_id, can_data=payload)
    assert secure_frame["freshness_value"] == 1
    assert len(secure_frame["mac"]) == 4
    
    # RX parses and accepts
    rx.receive_secure_frame(secure_frame)
    assert len(rx.received_messages) == 1
    assert rx.received_messages[0] == payload

def test_1202_invalid_mac_rejection(test_network):
    """TC-1202: Assert a Man-In-The-Middle bit flip is rejected."""
    tx, rx = test_network
    
    payload = b"\xFF\xFF\x00\x00\x11\x22\x33\x44"
    msg_id = 0x101
    secure_frame = tx.secure_transmit(message_id=msg_id, can_data=payload)
    
    # MITM attacker mutates the payload data byte 0 from 0xFF to 0xFE
    tampered_payload = b"\xFE\xFF\x00\x00\x11\x22\x33\x44"
    secure_frame["payload"] = tampered_payload
    
    with pytest.raises(MacValidationError) as excinfo:
         rx.receive_secure_frame(secure_frame)
    
    assert "MAC Mismatch" in str(excinfo.value)
    assert len(rx.received_messages) == 0

def test_1203_stale_freshness_value_rejection(test_network):
    """TC-1203: Assert replaying an older, cleanly recorded secure frame drops."""
    tx, rx = test_network
    
    # Cycle 1: Genuine Command sent and received
    cmd_1 = b"\xAA\xAA\xBB\xBB\xCC\xCC\xDD\xDD"
    msg_id_1 = 0x200
    frame_1 = tx.secure_transmit(message_id=msg_id_1, can_data=cmd_1)
    rx.receive_secure_frame(frame_1)
    assert len(rx.received_messages) == 1
    
    # Capture frame_1 for later Replay Attack
    recorded_attack_frame = dict(frame_1)
    
    # Cycle 2: Time passes, genuine new commands are sent
    cmd_2 = b"\x11\x11\x22\x22\x33\x33\x44\x44"
    frame_2 = tx.secure_transmit(message_id=msg_id_1, can_data=cmd_2)
    rx.receive_secure_frame(frame_2)
    assert len(rx.received_messages) == 2
    
    # Cycle 3: Attacker injects Cycle 1 back onto the bus
    # The payload and MAC mathematically align perfectly over the FV inside the frame!
    # But because recorded FV (1) <= RX current FV (2), it must be rejected natively.
    with pytest.raises(ReplayAttackError) as excinfo:
        rx.receive_secure_frame(recorded_attack_frame)
        
    assert "Stale Freshness Value detected: 1 <= 2" in str(excinfo.value)
    assert len(rx.received_messages) == 2 # Did not append

def test_1204_wrong_data_id_rejection(test_network):
    """TC-1204: Assert that replaying a valid MAC on a different CAN ID fails."""
    tx, rx = test_network
    
    payload = b"\x01\x02\x03\x04"
    original_id = 0x050
    # Create perfectly valid secure frame for ID 0x050
    secure_frame = tx.secure_transmit(message_id=original_id, can_data=payload)
    
    # Attacker intercepts the frame, leaves payload and MAC intact, 
    # but tries to inject it as a different message ID (e.g. 0x060)
    spoofed_frame = dict(secure_frame)
    spoofed_frame["message_id"] = 0x060
    
    with pytest.raises(MacValidationError) as excinfo:
        rx.receive_secure_frame(spoofed_frame)
        
    assert "MAC Mismatch" in str(excinfo.value)
    assert len(rx.received_messages) == 0

def test_1205_truncated_mac_validation(test_network):
    """TC-1205: Assert configurable MAC lengths strictly match and reject malformed truncations."""
    tx, rx = test_network
    
    payload = b"\xAA\xBB\xCC"
    msg_id = 0x111
    
    # Secure transmission with a 2-byte truncated MAC
    secure_frame = tx.secure_transmit(message_id=msg_id, can_data=payload, mac_length=2)
    assert len(secure_frame["mac"]) == 2
    
    # Positive validation: Receiver configured for 2-byte expects and parses correctly
    assert rx.receive_secure_frame(secure_frame) is True
    
    # Negative validation: Create a new frame but spoof the length field, forcing mismatch
    next_payload = b"\xDD\xEE\xFF"
    spoofed_length_frame = tx.secure_transmit(message_id=msg_id, can_data=next_payload, mac_length=3)
    
    # Attacker arbitrarily alters the size the receiver expects (if possible in their protocol)
    spoofed_length_frame["mac_length"] = 4 
    
    with pytest.raises(MacValidationError) as excinfo:
        rx.receive_secure_frame(spoofed_length_frame)
        
    assert "MAC trunctation mismatch. Expected 4 bytes, got 3" in str(excinfo.value)
