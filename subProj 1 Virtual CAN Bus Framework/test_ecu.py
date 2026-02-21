import time
import can
import pytest
from mock_ecu import MockECU

@pytest.fixture(scope="class")
def ecu_env():
    """Setup virtual CAN interface and start ECU instance for testing."""
    bus = can.Bus(channel='test_channel_1', interface='virtual')
    ecu = MockECU(channel='test_channel_1', interface='virtual')
    ecu.start()
    
    yield bus, ecu
    
    # Teardown
    ecu.stop()
    bus.shutdown()

class TestVirtualCANBus:
    
    @pytest.mark.req("REQ-001")
    def test_ecu_heartbeat_timing(self, ecu_env):
        """
        Test ID: TC-001
        Requirement: REQ-001 Validation
        The ECU shall broadcast message 0x100 every 20ms.
        Acceptable jitter tolerance: +/- 10ms in a virtualized, non-RTOS environment.
        """
        bus, _ = ecu_env
        
        # Clear buffer to get fresh timestamps
        while True:
            msg = bus.recv(timeout=0.01) # 10ms timeout ensures we break since frames are 20ms apart
            if msg is None:
                break
        
        times = []
        for _ in range(10):
            msg = bus.recv(timeout=1.0)
            assert msg is not None, "Message not received within timeout."
            assert msg.arbitration_id == 0x100, "Unexpected arbitration ID."
            times.append(msg.timestamp)
            
        intervals = [times[i] - times[i-1] for i in range(1, len(times))]
        
        for idx, interval in enumerate(intervals):
            # Assert interval is between 10ms and 30ms 
            assert 0.010 <= interval <= 0.030, f"Violation at cycle {idx}: time delta {interval:.4f}s"

    @pytest.mark.req("REQ-002")
    def test_ecu_payload_correctness(self, ecu_env):
        """
        Test ID: TC-002
        Requirement: REQ-002 Validation
        Message 0x100 shall contain Speed (byte 0) and RPM (bytes 1-2).
        """
        bus, ecu = ecu_env
        
        # Inject known values
        ecu.speed = 100
        ecu.rpm = 3500
        
        # Give thread time to construct the next message with new specific values
        time.sleep(0.05)
        
        # Read the message
        while True:
            msg = bus.recv(timeout=0.01)
            if msg is None:
                break
        msg = bus.recv(timeout=0.2)
        assert msg is not None
        
        speed = msg.data[0]
        rpm = (msg.data[1] << 8) | msg.data[2]
        
        assert speed == 100, f"Expected 100 km/h, got {speed}"
        assert rpm == 3500, f"Expected 3500 RPM, got {rpm}"

    @pytest.mark.req("REQ-003")
    def test_fault_injection_offline_node(self, ecu_env):
        """
        Test ID: TC-003
        Requirement: REQ-003 Validation
        Simulate an offline or defective node and ensure the testing framework identifies missing frames.
        """
        bus, ecu = ecu_env
        
        # Fault Injection: Stop the ECU thread (simulating a crash or power cut)
        # We manually halt the running loop without calling ecu.stop() to preserve the shared can.Bus object
        ecu.running = False
        if ecu.thread:
            ecu.thread.join()
        if hasattr(ecu, 'nm_thread') and ecu.nm_thread:
            ecu.nm_thread.join()
        
        # Wait expecting to timeout
        msg = bus.recv(timeout=0.100) # Wait for 100ms
        assert msg is None, "Expected timeout but received a message: ECU didn't stop successfully."
        
        # Recover environment for additional tests if needed
        ecu.start()
        # Brief sleep to allow thread to spin up and broadcast
        time.sleep(0.05)

    @pytest.mark.req("REQ-004")
    def test_out_of_bounds_signals(self, ecu_env):
        """
        Test ID: TC-004
        Requirement: REQ-004 Validation (Out of Range Bounds checking)
        ECU must floor/ceiling invalid speeds and RPMs.
        """
        bus, ecu = ecu_env
        
        # Inject out of bounds (Speed > 250, RPM > 8000)
        ecu.speed = 300
        ecu.rpm = 10000
        
        time.sleep(0.05)
        
        while True:
            if bus.recv(timeout=0.01) is None: break
        
        msg = bus.recv(timeout=0.2)
        assert msg is not None
        
        speed = msg.data[0]
        rpm = (msg.data[1] << 8) | msg.data[2]
        
        assert speed == 250, "Speed was not correctly ceilinged to 250 km/h."
        assert rpm == 8000, "RPM was not correctly ceilinged to 8000 RPM."

    @pytest.mark.req("REQ-005")
    def test_checksum_validation(self, ecu_env):
        """
        Test ID: TC-005
        Requirement: REQ-005 Validation
        Verify byte 7 contains a valid XOR checksum of bytes 0-6.
        """
        bus, ecu = ecu_env
        ecu.speed = 120
        ecu.rpm = 3000
        time.sleep(0.05)
        
        # We must simply await the very next message!
        # Clear out whatever might exist right now...
        while True:
            if bus.recv(timeout=0.01) is None: break
            
        # ...then wait for the actual freshly constructed ECU frame
        msg = bus.recv(timeout=0.2)
        assert msg is not None
        
        expected_checksum = 0
        for i in range(7):
            expected_checksum ^= msg.data[i]
            
        assert msg.data[7] == expected_checksum, "Checksum does not match XOR of payload."

    @pytest.mark.req("REQ-006")
    def test_network_management_sleep_wake(self, ecu_env):
        """
        Test ID: TC-006 (Phase 2 NM State Management)
        Requirement: REQ-006 Validation
        ECU must halt 0x100 transmission on Go-To-Sleep and resume on Wakeup.
        """
        bus, ecu = ecu_env
        
        # 1. Verify normal transmission
        msg = bus.recv(timeout=0.1)
        assert msg is not None, "ECU not transmitting in NORMAL state."
        
        # 2. Send Go-To-Sleep (0x600, byte[0] = 0x00)
        sleep_msg = can.Message(arbitration_id=0x600, data=[0x00])
        bus.send(sleep_msg)
        time.sleep(0.05) # Allow ECU to process NM command
        
        # 3. Assert no messages are received (Bus Sleep)
        while True:
            if bus.recv(timeout=0.01) is None: break
        
        msg = bus.recv(timeout=0.1)
        assert msg is None, "ECU ignored Go-To-Sleep command and continued transmitting."
        
        # 4. Send Wakeup (0x600, byte[0] = 0x01)
        wake_msg = can.Message(arbitration_id=0x600, data=[0x01])
        bus.send(wake_msg)
        time.sleep(0.05)
        
        # 5. Assert transmission resumed
        msg = bus.recv(timeout=0.1)
        assert msg is not None, "ECU did not resume transmission after Wakeup command."

    @pytest.mark.req("REQ-007")
    def test_babbling_idiot_detection(self, ecu_env):
        """
        Test ID: TC-007 (Phase 1 Robustness)
        Requirement: REQ-007 Validation
        Assert that the framework can detect a babbling idiot node saturating the bus.
        """
        bus, ecu = ecu_env
        
        # Instantiate a separate monitor node on the same virtual network
        monitor_bus = can.Bus(channel='test_channel_1', interface='virtual')
        
        # Clear monitor buffer
        while True:
            if monitor_bus.recv(timeout=0.01) is None: break
            
        # Simulate a rogue node flooding the bus
        for i in range(100):
            bus.send(can.Message(arbitration_id=0x100, data=[0]*8))
            
        messages_received = 0
        while monitor_bus.recv(timeout=0.01) is not None:
            messages_received += 1
                
        monitor_bus.shutdown()
        
        # Normally we expect 0 or 1 message from the normal ECU in this split microsecond. 
        # Since we flooded it, the monitor buffer should yield close to 100 instantly.
        assert messages_received > 50, f"Babbling idiot simulation failed to saturate. Got {messages_received}"
