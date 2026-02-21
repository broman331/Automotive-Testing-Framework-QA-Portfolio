class FaultMode:
    NONE = "NONE"
    DROP_ALL = "DROP_ALL"
    LATENCY = "LATENCY"
    CORRUPT_PAYLOAD = "CORRUPT_PAYLOAD"
    STALE_DATA = "STALE_DATA"
    CORRUPT_CRC = "CORRUPT_CRC"
    DUPLICATE_FRAME = "DUPLICATE_FRAME"

class FaultProxy:
    """
    Man-In-The-Middle CAN router that sabotages messages between Sensors and ECUs.
    """
    def __init__(self):
        self.mode = FaultMode.NONE
        self.latency_ms = 0
        self.stale_speed = None
        self.stuck_counter = 0
        self.last_sequence_number = -1

    def set_fault_mode(self, mode: str, latency_ms: int = 0):
        self.mode = mode
        self.latency_ms = latency_ms
        if mode == FaultMode.STALE_DATA:
            self.stale_speed = None # Will grab the next frame
            self.stuck_counter = 0

    def intercept_and_process(self, speed_kph: int, sequence_number: int, crc_checksum: int):
        """Processes the intercepted message and returns the sabotaged payload, or None if dropped."""
        if self.mode == FaultMode.DROP_ALL:
            return None
            
        elif self.mode == FaultMode.LATENCY:
            # In a real async system, this would push to a queue and a worker would pop it later.
            # For our synchronous tick-based test harness, we simulate by dropping it now, and the 
            # test harness advances time to trigger the ECU's deadline violation.
            pass 
            
        elif self.mode == FaultMode.CORRUPT_PAYLOAD:
            # Bit-flip simulation: Turn 11 (0000 1011) into 139 (1000 1011)
            corrupted_speed = speed_kph | 0x80 # Flip the highest bit
            # We must recalculate the CRC for the new payload, otherwise the ECU drops it at the E2E layer
            # and never calculates our intended Implausible Signal physics test.
            new_crc = (corrupted_speed ^ sequence_number) & 0xFF
            return (corrupted_speed, sequence_number, new_crc)
            
        elif self.mode == FaultMode.STALE_DATA:
            if self.stale_speed is None:
                self.stale_speed = speed_kph # Freeze on the first value
                
            # Recalculate CRC using the frozen speed but the natively incremented sequence
            stuck_crc = (self.stale_speed ^ sequence_number) & 0xFF
            return (self.stale_speed, sequence_number, stuck_crc)
            
        elif self.mode == FaultMode.CORRUPT_CRC:
            # Re-calculate a completely garbage Checksum instead of the expected one
            bad_crc = (crc_checksum + 1) % 256
            return (speed_kph, sequence_number, bad_crc)
            
        elif self.mode == FaultMode.DUPLICATE_FRAME:
            if self.last_sequence_number == -1:
                self.last_sequence_number = sequence_number
                return (speed_kph, sequence_number, crc_checksum)
                
            # Proxy forces the sequence counter to be exactly what it was last time
            corrupt_seq = self.last_sequence_number
            # CRC must be recalculated because sequence changed, or ECU trips the CRC error instead!
            new_crc = (speed_kph ^ corrupt_seq) & 0xFF
            return (speed_kph, corrupt_seq, new_crc)
            
        # Normal Mode
        self.last_sequence_number = sequence_number
        return (speed_kph, sequence_number, crc_checksum)
        
    def tick(self, dt_ms: int):
        pass
