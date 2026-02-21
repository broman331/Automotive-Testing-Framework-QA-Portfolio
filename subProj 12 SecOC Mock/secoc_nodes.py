import struct
from secoc_crypto import SecOCEngine, MacValidationError, ReplayAttackError

class TransmitterECU:
    def __init__(self, key: bytes):
        self.crypto = SecOCEngine(key)

    def secure_transmit(self, can_data: bytes) -> dict:
        """
        Simulates securing a CAN PDU. 
        Returns a dictionary representing the CAN frame construction.
        """
        # In real life, the transmitter requests FV from the SecOC manager
        self.crypto.increment_freshness()
        fv = self.crypto.get_freshness_value()
        
        # Generate truncated 4-byte MAC
        mac = self.crypto.generate_mac(can_data, fv, mac_length=4)
        
        # Construct the "Secured PDU"
        return {
            "payload": can_data,
            "freshness_value": fv, # Sent out of band, or truncated in the frame
            "mac": mac
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
        payload = frame.get("payload")
        fv = frame.get("freshness_value")
        mac = frame.get("mac")
        
        # The crypto engine internally asserts Replay and MAC Logic
        if self.crypto.verify_mac(payload, fv, mac):
            self.received_messages.append(payload)
            return True
