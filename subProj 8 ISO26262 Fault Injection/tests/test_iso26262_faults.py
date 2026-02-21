import pytest
from fault_proxy import FaultProxy, FaultMode
from safety_ecu import SafetyECU, SafeState
import time

class VirtualHardwareSimulator:
    """Mock testing harness to pass messages from the 'Sensor' through the Proxy to the 'ECU'."""
    def __init__(self):
        self.proxy = FaultProxy()
        self.ecu = SafetyECU()
        
    def send_sensor_data(self, speed_kph: int, sequence_number: int):
        """Simulate a raw sensor reading dispatched onto the CAN bus."""
        # Calculate a mock 8-bit CRC checksum for the E2E profile
        crc_checksum = (speed_kph ^ sequence_number) & 0xFF
        
        # 1. The Proxy intercepts the physical layer transmission
        corrupted_payload = self.proxy.intercept_and_process(speed_kph, sequence_number, crc_checksum)
        
        # 2. If the proxy dropped the frame entirely, the ECU receives nothing
        if corrupted_payload is not None:
             # The Proxy forwards to the ECU
             corrupt_speed, corrupt_seq, corrupt_crc = corrupted_payload
             self.ecu.on_sensor_message_received(corrupt_speed, corrupt_seq, corrupt_crc)

    def tick_all(self, dt_ms: int):
        self.proxy.tick(dt_ms)
        self.ecu.tick(dt_ms)


@pytest.fixture
def sim():
    return VirtualHardwareSimulator()

# -------------------------------------------------------------
# Part 1: Availability Faults (Network Disruption)
# -------------------------------------------------------------
def test_801_total_signal_loss(sim):
    """TC-801: Wire Cut Simulation"""
    # System starts healthy
    sim.send_sensor_data(speed_kph=50, sequence_number=1)
    assert sim.ecu.state == SafeState.NORMAL_OPERATION
    
    # INJECT FAULT: The wire is cut.
    sim.proxy.set_fault_mode(FaultMode.DROP_ALL)
    
    # 5 frames are transmitted by the sensor over 100ms, but all are dropped by the proxy
    for i in range(5):
        sim.send_sensor_data(speed_kph=50, sequence_number=i+2)
        sim.tick_all(20) # 20ms cycle
        
    # ECU timeout limit is 50ms. After 100ms of silence, it must enter COM_LOSS mode.
    assert sim.ecu.state == SafeState.SAFE_STATE_COM_LOSS

def test_802_high_latency_congestion(sim):
    """TC-802: CPU Overload / Network Congestion Simulation"""
    # System starts healthy
    sim.send_sensor_data(speed_kph=50, sequence_number=1)
    
    # INJECT FAULT: Add 100ms latency to all frames
    sim.proxy.set_fault_mode(FaultMode.LATENCY, latency_ms=100)
    
    # Sensor transmits exactly on time (20ms later)
    sim.send_sensor_data(speed_kph=50, sequence_number=2)
    
    # Advance time by 40ms. ECU should have received the frame by now, but it's stuck in Proxy Buffer
    sim.tick_all(40)
    
    # Because of the timeline jitter, the ECU detects a violation before the message finally arrives
    assert sim.ecu.state == SafeState.TIMING_VIOLATION


# -------------------------------------------------------------
# Part 2: Integrity Faults (Data Corruption)
# -------------------------------------------------------------
def test_803_bit_flipping_emi(sim):
    """TC-803: Electromagnetic Interference simulating radical sensor spikes"""
    sim.send_sensor_data(speed_kph=10, sequence_number=1)
    assert sim.ecu.state == SafeState.NORMAL_OPERATION
    
    # INJECT FAULT: Corrupt the payload bits
    sim.proxy.set_fault_mode(FaultMode.CORRUPT_PAYLOAD)
    
    # Sensor transmits correct 11km/h
    # Proxy flips the high-order bits turning 11 into 139
    sim.send_sensor_data(speed_kph=11, sequence_number=2)
    sim.tick_all(20)
    
    # ECU calculates Delta(139, 10) = 129km/h jump in 20ms. Impossible physics.
    assert sim.ecu.state == SafeState.IMPLAUSIBLE_SIGNAL

def test_804_stuck_sensor_stale_data(sim):
    """TC-804: Sensor ADC locks up, but CAN transceiver keeps sending frozen data"""
    sim.send_sensor_data(speed_kph=60, sequence_number=1)
    sim.tick_all(20)
    
    # INJECT FAULT: Stale Data
    sim.proxy.set_fault_mode(FaultMode.STALE_DATA)
    
    # We transmit changing speed profiles, but the Proxy forces the data to stay at 60
    sim.send_sensor_data(speed_kph=61, sequence_number=2)
    sim.tick_all(20)
    sim.send_sensor_data(speed_kph=62, sequence_number=3)
    sim.tick_all(20)
    sim.send_sensor_data(speed_kph=63, sequence_number=4)
    sim.tick_all(20)
    sim.send_sensor_data(speed_kph=64, sequence_number=5)
    sim.tick_all(20)

    # After N cycles of identically frozen data despite moving sequence numbers, ECU flags Stale Error
    assert sim.ecu.state == SafeState.STALE_DATA

# -------------------------------------------------------------
# Part 3: E2E Protection (AUTOSAR Profile 1)
# -------------------------------------------------------------
def test_805_e2e_crc_checksum_failure(sim):
    """TC-805: Proxy recalculates an intentionally invalid CRC"""
    sim.send_sensor_data(speed_kph=40, sequence_number=1)
    assert sim.ecu.state == SafeState.NORMAL_OPERATION
    
    # INJECT FAULT: Corrupt the CRC Checksum
    sim.proxy.set_fault_mode(FaultMode.CORRUPT_CRC)
    
    sim.send_sensor_data(speed_kph=40, sequence_number=2)
    sim.tick_all(20)
    
    # ECU calculates its own CRC and finds a mismatch with the received CRC
    assert sim.ecu.state == SafeState.E2E_CRC_ERROR

def test_806_e2e_sequence_duplication(sim):
    """TC-806: Proxy duplicates a frame representing a Replay Attack or gateway routing loop"""
    sim.send_sensor_data(speed_kph=60, sequence_number=1)
    
    # INJECT FAULT: Duplicate the specific Sequence Counter
    sim.proxy.set_fault_mode(FaultMode.DUPLICATE_FRAME)
    
    # Sensor natively sends Sequence 2, but Proxy overrides it and transmits Sequence 1 again
    sim.send_sensor_data(speed_kph=60, sequence_number=2)
    sim.tick_all(20)
    
    # ECU recognizes `last_seq == current_seq`
    assert sim.ecu.state == SafeState.E2E_SEQ_DUPLICATION
