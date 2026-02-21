import pytest
import struct
import can
from xcp_ecu import XcpSlaveNode, XcpError
from xcp_master import XcpMaster

@pytest.fixture
def xcp_network():
    # Setup mock network
    node_id = 0x600
    slave = XcpSlaveNode(node_id=node_id)
    master = XcpMaster(target_node_id=node_id)
    return master, slave

def test_901_xcp_connection_lifecycle(xcp_network):
    """TC-901: XCP Connection Lifecycle"""
    master, slave = xcp_network
    
    # 1. Reject commands before connection
    cro = master.create_set_mta_cro(0x1000)
    dto = slave.process_cro(cro)
    response = master.parse_dto_response(dto)
    
    assert response["status"] == "ERR"
    assert response["error_code"] == XcpError.ERR_CMD_IGNORED
    assert slave.is_connected == False
    
    # 2. Establish Connection
    cro = master.create_connect_cro()
    dto = slave.process_cro(cro)
    response = master.parse_dto_response(dto)
    
    assert response["status"] == "RES" # Positive Response
    assert slave.is_connected == True
    
    # 3. Disconnect
    cro = master.create_disconnect_cro()
    dto = slave.process_cro(cro)
    response = master.parse_dto_response(dto)
    
    assert response["status"] == "RES"
    assert slave.is_connected == False

def test_902_calibration_memory_upload(xcp_network):
    """TC-902: Calibration Memory Upload (Read) - Reading Speed Limit (0x1000)"""
    master, slave = xcp_network
    
    # Connect
    slave.process_cro(master.create_connect_cro())
    
    # Set Memory Transfer Address (MTA) to 0x1000
    cro = master.create_set_mta_cro(address=0x1000)
    dto = slave.process_cro(cro)
    assert master.parse_dto_response(dto)["status"] == "RES"
    
    # Upload (Read) 4 bytes
    cro = master.create_upload_cro(num_bytes=4)
    dto = slave.process_cro(cro)
    response = master.parse_dto_response(dto)
    
    assert response["status"] == "RES"
    # Unpack the little-endian 4-byte payload back to an integer
    # response['payload'] includes the rest of the padding (up to 7 bytes total). 
    # Extract the first 4 bytes.
    read_payload = response["payload"][:4]
    speed_limit = struct.unpack("<I", read_payload)[0]
    
    assert speed_limit == 120 # Default value setup in xcp_ecu.py

def test_903_calibration_memory_download(xcp_network):
    """TC-903: Calibration Memory Download (Write) - Mutating AEB Gain (0x1004)"""
    master, slave = xcp_network
    slave.process_cro(master.create_connect_cro())
    
    # Set MTA to 0x1004 (AEB Braking Gain)
    slave.process_cro(master.create_set_mta_cro(address=0x1004))
    
    # Download (Write) New Payload (e.g. tuning gain from 850 up to 990)
    new_gain_bytes = struct.pack("<I", 990)
    cro = master.create_download_cro(data_bytes=new_gain_bytes)
    dto = slave.process_cro(cro)
    
    assert master.parse_dto_response(dto)["status"] == "RES"
    
    # Now verify the memory physically changed in the ECU
    assert struct.unpack("<I", slave.memory[0x1004])[0] == 990
    
    # Also verify via an explicit UPLOAD command just to be thorough
    slave.process_cro(master.create_set_mta_cro(address=0x1004))
    dto = slave.process_cro(master.create_upload_cro(num_bytes=4))
    read_val = struct.unpack("<I", master.parse_dto_response(dto)["payload"][:4])[0]
    
    assert read_val == 990
