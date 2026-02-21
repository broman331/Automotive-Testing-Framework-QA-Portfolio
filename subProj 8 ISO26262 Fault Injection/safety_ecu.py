class SafeState:
    NORMAL_OPERATION = "NORMAL_OPERATION"
    SAFE_STATE_COM_LOSS = "SAFE_STATE_COM_LOSS"
    TIMING_VIOLATION = "TIMING_VIOLATION"
    IMPLAUSIBLE_SIGNAL = "IMPLAUSIBLE_SIGNAL"
    STALE_DATA = "STALE_DATA"
    E2E_CRC_ERROR = "E2E_CRC_ERROR"
    E2E_SEQ_DUPLICATION = "E2E_SEQ_DUPLICATION"

class SafetyECU:
    """
    ISO 26262 compliant receiving module that degrades gracefully when signal inputs fail.
    """
    def __init__(self):
        self.state = SafeState.NORMAL_OPERATION
        self.last_speed = 0
        self.last_seq = -1
        
        # ISO 26262 Safety Counters
        self.time_since_last_msg_ms = 0
        self.stale_data_counter = 0
        
        # Safety Constraints
        self.MAX_TIMEOUT_MS = 50
        self.MAX_STALE_CYCLES = 3
        self.MAX_DELTAV_PER_CYCLE = 30 # Impossible to accelerate/brake more than 30kph in 20ms

    def on_sensor_message_received(self, speed_kph: int, sequence_number: int, crc_checksum: int):
        # 0. E2E (End to End) Protection Profile 1 Checks
        expected_crc = (speed_kph ^ sequence_number) & 0xFF
        if crc_checksum != expected_crc:
            self.state = SafeState.E2E_CRC_ERROR
            return # Drop invalid frame entirely
            
        if sequence_number == self.last_seq:
            self.state = SafeState.E2E_SEQ_DUPLICATION
            return # Drop duplicated frames
            
        # 1. Check for Timing Violations (Jitter > max allowed)
        if self.time_since_last_msg_ms > self.MAX_TIMEOUT_MS:
            if self.state != SafeState.SAFE_STATE_COM_LOSS: 
                self.state = SafeState.TIMING_VIOLATION
            # Keep tracking other errors even if timing is bad
            
        # 2. Check for Implausible Plausibility (Delta > max physics)
        delta_v = abs(speed_kph - self.last_speed)
        if delta_v > self.MAX_DELTAV_PER_CYCLE and self.last_seq != -1:
            self.state = SafeState.IMPLAUSIBLE_SIGNAL
            
        # 3. Check for Stale/Frozen data
        if speed_kph == self.last_speed and sequence_number > self.last_seq and self.last_seq != -1:
            self.stale_data_counter += 1
            if self.stale_data_counter >= self.MAX_STALE_CYCLES:
                self.state = SafeState.STALE_DATA
        else:
            self.stale_data_counter = 0 # Reset counter if data changes
            
        # Update trackers
        self.last_speed = speed_kph
        self.last_seq = sequence_number
        self.time_since_last_msg_ms = 0 # Reset timer

    def tick(self, dt_ms: int):
        self.time_since_last_msg_ms += dt_ms
        
        # Timing Violation (Jitter but not COM Loss yet)
        if self.time_since_last_msg_ms > 20 and self.time_since_last_msg_ms <= self.MAX_TIMEOUT_MS:
             if self.state == SafeState.NORMAL_OPERATION:
                 self.state = SafeState.TIMING_VIOLATION

        # Total Communication Loss Evaluation
        if self.time_since_last_msg_ms > self.MAX_TIMEOUT_MS:
            # We haven't heard from the sensor in over 50ms. Safety critical failure.
            self.state = SafeState.SAFE_STATE_COM_LOSS
