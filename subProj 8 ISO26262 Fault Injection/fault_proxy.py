class FaultMode:
    NONE = "NONE"
    DROP_ALL = "DROP_ALL"
    LATENCY = "LATENCY"
    CORRUPT_PAYLOAD = "CORRUPT_PAYLOAD"
    STALE_DATA = "STALE_DATA"

class FaultProxy:
    """
    Man-In-The-Middle CAN router that sabotages messages between Sensors and ECUs.
    """
    def __init__(self):
        self.mode = FaultMode.NONE
        self.latency_ms = 0
        self.stale_speed = None
        self.stuck_counter = 0

    def set_fault_mode(self, mode: str, latency_ms: int = 0):
        self.mode = mode
        self.latency_ms = latency_ms
        if mode == FaultMode.STALE_DATA:
            self.stale_speed = None # Will grab the next frame
            self.stuck_counter = 0

    def intercept_and_process(self, speed_kph: int, sequence_number: int):
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
            return (corrupted_speed, sequence_number)
            
        elif self.mode == FaultMode.STALE_DATA:
            if self.stale_speed is None:
                self.stale_speed = speed_kph # Freeze on the first value
                
            # The sensor tries to send a new speed, but the proxy overwrites the payload 
            # with the frozen value, while keeping the sequence number climbing natively.
            return (self.stale_speed, sequence_number)
            
        # Normal Mode
        return (speed_kph, sequence_number)
        
    def tick(self, dt_ms: int):
        pass
