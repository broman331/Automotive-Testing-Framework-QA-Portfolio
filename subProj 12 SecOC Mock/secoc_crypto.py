import hmac
import hashlib
import struct

class MacValidationError(Exception):
    """Raised when a computed MAC doesn't match the received MAC."""
    pass

class ReplayAttackError(Exception):
    """Raised when a received Freshness Value is older than or equal to the current one."""
    pass

class SecOCEngine:
    """Mock Cryptographic Engine for AUTOSAR SecOC."""
    
    def __init__(self, secret_key: bytes):
        """Initialize with a shared 128-bit key (represented as 16 bytes)."""
        if len(secret_key) != 16:
            raise ValueError("Secret key must be 16 bytes for AES-128 approximation.")
        self.secret_key = secret_key
        # Normally FV is synced via a complex time/counter mechanism, we simulate a monotonic counter.
        self.current_fv = 0

    def get_freshness_value(self) -> int:
        """Returns the synchronized monotonic Freshness Value."""
        return self.current_fv

    def increment_freshness(self):
        """Tick the FV counter. In real life, this is often synced by a master clock."""
        self.current_fv += 1

    def generate_mac(self, data_payload: bytes, freshness_value: int, mac_length: int = 4) -> bytes:
        """
        Simulates AES-CMAC by generating an HMAC-SHA256 signature over 
        (Data + FreshnessValue) and trunking it to `mac_length` bytes.
        """
        # Pack FV as a 32-bit big-endian integer
        fv_bytes = struct.pack(">I", freshness_value)
        data_to_sign = data_payload + fv_bytes
        
        # Calculate full HMAC (Simulating CMAC)
        full_mac = hmac.new(self.secret_key, data_to_sign, hashlib.sha256).digest()
        
        # Truncate MAC (e.g. AUTOSAR profile 1 uses 3-4 byte MACs to fit in CAN frames)
        return full_mac[:mac_length]

    def verify_mac(self, received_payload: bytes, received_fv: int, received_mac: bytes) -> bool:
        """
        Verifies that the MAC matches the payload+FV combination.
        Raises specific security exceptions on failure.
        """
        # 1. Check against Replay Attacks
        if received_fv <= self.current_fv:
             raise ReplayAttackError(f"Stale Freshness Value detected: {received_fv} <= {self.current_fv}")
        
        # 2. Verify MAC Cryptography
        expected_mac = self.generate_mac(received_payload, received_fv, len(received_mac))
        if hmac.compare_digest(expected_mac, received_mac):
            # Valid! Sync the internal FV to the new valid one
            self.current_fv = received_fv
            return True
        else:
            raise MacValidationError(f"MAC Mismatch. Expected: {expected_mac.hex()}, Got: {received_mac.hex()}")

