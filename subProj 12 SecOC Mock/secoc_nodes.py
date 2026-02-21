import struct
from secoc_crypto import SecOCEngine, MacValidationError, ReplayAttackError

class TransmitterECU:
    def __init__(self, key: bytes):
        self.crypto = SecOCEngine(key)

    def secure_transmit(self, message_id: int, can_data: bytes, mac_length: int = 4) -> dict:
        """
        Simulates securing a CAN PDU. 
        Returns a dictionary representing the CAN frame construction.
        """
        # In real life, the transmitter requests FV from the SecOC manager
        self.crypto.increment_freshness()
        fv = self.crypto.get_freshness_value()
        
        # Generate truncated MAC natively bound to the CAN ID
        mac = self.crypto.generate_mac(message_id, can_data, fv, mac_length=mac_length)
        
        # Construct the "Secured PDU"
        return {
            "message_id": message_id,
            "payload": can_data,
            "freshness_value": fv, # Sent out of band, or truncated in the frame
            "mac": mac,
            "mac_length": mac_length
        }

class ReceiverECU:
    def __init__(self, key: bytes):
        self.crypto = SecOCEngine(key)
        self.received_messages = []

    def receive_secure_frame(self, frame: dict):
        """
        Validates an incoming PDU dictionary. 
        Raises exceptions strictly on failure.
        """
        message_id = frame.get("message_id")
        payload = frame.get("payload")
        fv = frame.get("freshness_value")
        mac = frame.get("mac")
        expected_mac_len = frame.get("mac_length", 4)

        if len(mac) != expected_mac_len:
            raise MacValidationError(f"MAC trunctation mismatch. Expected {expected_mac_len} bytes, got {len(mac)}")
        
        # The crypto engine internally asserts Replay and MAC Logic bound to the CAN ID
        if self.crypto.verify_mac(message_id, payload, fv, mac):
            self.received_messages.append(payload)
            return True
