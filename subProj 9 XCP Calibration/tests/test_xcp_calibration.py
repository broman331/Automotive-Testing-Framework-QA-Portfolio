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

def test_902_protected_memory_access_denied(xcp_network):
    """TC-902: Protected Memory Access Denied - Attempt to write without unlocking"""
    master, slave = xcp_network
    slave.process_cro(master.create_connect_cro())
    
    slave.process_cro(master.create_set_mta_cro(address=0x1004))
    
    new_gain_bytes = struct.pack("<I", 990)
    cro = master.create_download_cro(data_bytes=new_gain_bytes)
    dto = slave.process_cro(cro)
    response = master.parse_dto_response(dto)
    
    assert response["status"] == "ERR"
    assert response["error_code"] == XcpError.ERR_ACCESS_DENIED

def test_903_seed_and_key_authentication(xcp_network):
    """TC-903: Seed & Key Authentication"""
    master, slave = xcp_network
    slave.process_cro(master.create_connect_cro())
    
    cro = master.create_get_seed_cro(mode=0x00)
    dto = slave.process_cro(cro)
    response = master.parse_dto_response(dto)
    
    assert response["status"] == "RES"
    seed_bytes = response["payload"][1:5]
    seed = struct.unpack(">I", seed_bytes)[0]
    
    # Compute Key (Mock algorithm: XOR 0xDEADBEEF)
    key = seed ^ 0xDEADBEEF
    key_bytes = struct.pack(">I", key)
    
    cro = master.create_unlock_cro(key_bytes)
    dto = slave.process_cro(cro)
    response = master.parse_dto_response(dto)
    
    assert response["status"] == "RES"
    assert slave.is_unlocked == True

def test_904_calibration_memory_upload(xcp_network):
    """TC-904: Calibration Memory Upload (Read) - Reading Speed Limit (0x1000)"""
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
    read_payload = response["payload"][:4]
    speed_limit = struct.unpack("<I", read_payload)[0]
    
    assert speed_limit == 120 # Default value setup in xcp_ecu.py

def test_905_calibration_memory_download(xcp_network):
    """TC-905: Calibration Memory Download (Write) - Mutating AEB Gain (0x1004)"""
    master, slave = xcp_network
    slave.process_cro(master.create_connect_cro())
    
    # Authenticate to write to protected memory
    dto = slave.process_cro(master.create_get_seed_cro(mode=0x00))
    seed = struct.unpack(">I", master.parse_dto_response(dto)["payload"][1:5])[0]
    key_bytes = struct.pack(">I", seed ^ 0xDEADBEEF)
    slave.process_cro(master.create_unlock_cro(key_bytes))
    
    # Set MTA to 0x1004 (AEB Braking Gain)
    slave.process_cro(master.create_set_mta_cro(address=0x1004))
    
    # Download (Write) New Payload
    new_gain_bytes = struct.pack("<I", 990)
    cro = master.create_download_cro(data_bytes=new_gain_bytes)
    dto = slave.process_cro(cro)
    
    assert master.parse_dto_response(dto)["status"] == "RES"
    
    # Verify memory physically changed
    assert struct.unpack("<I", slave.memory[0x1004])[0] == 990

def test_906_short_upload_optimization(xcp_network):
    """TC-906: Short Upload Optimization"""
    master, slave = xcp_network
    slave.process_cro(master.create_connect_cro())
    
    # Read Speed Limit straight from 0x1000 using 1 command
    cro = master.create_short_upload_cro(num_bytes=4, address=0x1000)
    dto = slave.process_cro(cro)
    response = master.parse_dto_response(dto)
    
    assert response["status"] == "RES"
    read_payload = response["payload"][:4]
    speed_limit = struct.unpack("<I", read_payload)[0]
    
    assert speed_limit == 120
    # Also verify that the pointer (MTA) updated
    assert slave.mta == 0x1000
