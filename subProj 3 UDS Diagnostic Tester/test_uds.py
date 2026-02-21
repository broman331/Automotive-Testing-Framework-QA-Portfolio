import pytest
import time
import can
import isotp
from udsoncan.connections import PythonIsoTpConnection
from udsoncan.client import Client
from udsoncan import configs
from udsoncan.exceptions import NegativeResponseException
from udsoncan import AsciiCodec
from uds_ecu import MockUDSECU

# Security algorithm generating the exact Key MockECU expects
def dummy_security_algo(level, seed, params):
    return bytes([0x55, 0x44, 0x33, 0x22])

@pytest.fixture(scope="module")
def uds_env():
    # 1. Start the Virtual ECU thread
    ecu = MockUDSECU(channel='test_uds_bus', interface='virtual')
    ecu.start()
    time.sleep(0.1)  # Allow thread to boot
    
    # 2. Configure the ISO-TP Transport Layer for the Client
    # Client transmits to 0x7E0, ECU transmits to 0x7E8 (standard 11-bit)
    client_bus = can.Bus(channel='test_uds_bus', interface='virtual')
    client_stack = isotp.CanStack(
        client_bus,
        address=isotp.Address(isotp.AddressingMode.Normal_11bits, rxid=0x7E8, txid=0x7E0)
    )
    conn = PythonIsoTpConnection(client_stack)
    
    # 3. Configure UDSonCAN Client 
    client_config = dict(configs.default_client_config)
    client_config['data_identifiers'] = {
        0xF190: AsciiCodec(17) # VIN length mapping for Pytest decoder
    }
    client_config['security_algo'] = dummy_security_algo
    
    with Client(conn, config=client_config) as client:
        yield client # Pass client to test functions
        
    # Teardown
    ecu.stop()

class TestUDSProtocolFuzzer:
    
    # ----------------------------------------------------
    # PART 1: Valid Sequence Flows (Positive Tests)
    # ----------------------------------------------------
    
    @pytest.mark.req("TC-301")
    def test_valid_rdbi_vin(self, uds_env):
        """Test ID: TC-301 - Request standard VIN DID 0xF190"""
        response = uds_env.read_data_by_identifier(didlist=[0xF190])
        assert response.service_data.values[0xF190] == "WBA00000000000000"

    @pytest.mark.req("TC-302")
    def test_session_transition(self, uds_env):
        """Test ID: TC-302 - Valid transition to Extended Session"""
        response = uds_env.change_session(0x03)
        assert response.positive

    @pytest.mark.req("TC-303")
    def test_security_access_unlock(self, uds_env):
        """Test ID: TC-303 - Authenticate using Seed/Key unlocking"""
        # UDSonCAN auto-requests seed (0x01) and sends calculated key (0x02)
        response = uds_env.unlock_security_access(level=1)
        assert response.positive

    @pytest.mark.req("TC-309")
    def test_ecu_hard_reset(self, uds_env):
        """Test ID: TC-309 - Trigger ECU Hard Reset (0x11 0x01)"""
        response = uds_env.ecu_reset(reset_type=1)
        assert response.positive

    @pytest.mark.req("TC-310")
    def test_clear_dtc(self, uds_env):
        """Test ID: TC-310 - Clear Diagnostic Information (0x14 0xFFFFFF)"""
        response = uds_env.clear_dtc(group=0xFFFFFF)
        assert response.positive

    @pytest.mark.req("TC-311")
    def test_tester_present(self, uds_env):
        """Test ID: TC-311 - Tester Present keep-alive (0x3E 0x00)"""
        response = uds_env.tester_present()
        assert response.positive

    # ----------------------------------------------------
    # PART 2: Fuzzing & Negative Response Code (NRC) Assertions
    # ----------------------------------------------------
    
    @pytest.mark.req("TC-304")
    def test_invalid_subfunction_nrc(self, uds_env):
        """Test ID: TC-304 - Fuzz session with unsupported subfunction 0x04"""
        with pytest.raises(NegativeResponseException) as excinfo:
            uds_env.change_session(0x04)
        # Assert NRC 0x12: SubFunction Not Supported
        assert excinfo.value.response.code == 0x12 
        
    @pytest.mark.req("TC-305")
    def test_incorrect_msg_length_nrc(self, uds_env):
        """Test ID: TC-305 - Fuzz 0x22 payload by illegally truncating it"""
        # Truncate RDBI payload to just 2 bytes (0x22 0xF1) instead of 3
        # Direct raw transmission via ISO-TP to bypass UDSonCAN protections
        uds_env.conn.send(b'\x22\xF1')
        raw_resp = uds_env.conn.wait_frame(timeout=1.0)
        
        # Assert Negative Response (0x7F) for SID (0x22) with NRC (0x13 - IncorrectMsgLength)
        assert raw_resp == b'\x7F\x22\x13'

    @pytest.mark.req("TC-306")
    def test_request_sequence_error_nrc(self, uds_env):
        """Test ID: TC-306 - Fuzz Security Access by skipping Seed Request"""
        # Directly send SendKey (0x02) without a preceding RequestSeed (0x01)
        uds_env.conn.send(b'\x27\x02\x55\x44\x33\x22')
        raw_resp = uds_env.conn.wait_frame(timeout=1.0)
        
        # Assert NRC (0x24 - Request Sequence Error)
        assert raw_resp == b'\x7F\x27\x24'

    @pytest.mark.req("TC-307")
    def test_security_access_denied_nrc(self, uds_env):
        """Test ID: TC-307 - Attempt unlock with invalid calculated Key"""
        uds_env.conn.send(b'\x27\x01') # Request seed
        raw_seed_resp = uds_env.conn.wait_frame(timeout=1.0)
        assert raw_seed_resp[0] == 0x67 # Verify Seed Positive Response
        
        # Send garbage key '00 00 00 00' instead of '55 44 33 22'
        uds_env.conn.send(b'\x27\x02\x00\x00\x00\x00')
        raw_key_resp = uds_env.conn.wait_frame(timeout=1.0)
        
        # Assert NRC (0x33 - Security Access Denied)
        assert raw_key_resp == b'\x7F\x27\x33'

    @pytest.mark.req("TC-308")
    def test_request_out_of_range_nrc(self, uds_env):
        """Test ID: TC-308 - Fuzz RDBI by targeting restricted memory addresses"""
        with pytest.raises(NegativeResponseException) as excinfo:
            # Try to read Did 0xFFFF, which the ECU does not map/allow
            # Create a dummy config entry so the client doesn't complain locally
            uds_env.config['data_identifiers'][0xFFFF] = AsciiCodec(1)
            uds_env.read_data_by_identifier(didlist=[0xFFFF])
            
        # Assert NRC 0x31: Request Out Of Range
        assert excinfo.value.response.code == 0x31
