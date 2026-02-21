import struct
import can

class XcpMaster:
    """
    Automated Testing Tool that sends Universal Measurement and Calibration Protocol (XCP) 
    commands to a subordinate ECU.
    """
    def __init__(self, target_node_id: int):
        self.target_node_id = target_node_id
        
    def create_connect_cro(self) -> can.Message:
        """Builds a CONNECT packet."""
        data = [0xFF, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
        return self._build_cro(data)

    def create_disconnect_cro(self) -> can.Message:
        """Builds a DISCONNECT packet."""
        data = [0xFE, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
        return self._build_cro(data)

    def create_set_mta_cro(self, address: int) -> can.Message:
        """Builds a SET_MTA packet to set the memory pointer."""
        addr_bytes = struct.pack(">I", address) # Big Endian 4-byte address
        data = [0xF6, 0x00, 0x00, 0x00, addr_bytes[0], addr_bytes[1], addr_bytes[2], addr_bytes[3]]
        return self._build_cro(data)

    def create_upload_cro(self, num_bytes: int) -> can.Message:
        """Builds an UPLOAD packet to read memory from the current MTA."""
        data = [0xF5, num_bytes, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
        return self._build_cro(data)

    def create_download_cro(self, data_bytes: bytes) -> can.Message:
        """Builds a DOWNLOAD packet to flash memory to the current MTA."""
        num_bytes = len(data_bytes)
        data = [0xF0, num_bytes] + list(data_bytes)
        # Pad to 8
        while len(data) < 8:
            data.append(0x00)
        return self._build_cro(data[:8])

    def parse_dto_response(self, message: can.Message) -> dict:
        """Parses a Data Transmission Object (DTO) string returned by the ECU."""
        pid = message.data[0]
        if pid == 0xFF:
            return {"status": "RES", "payload": bytes(message.data[1:])}
        elif pid == 0xFE:
            return {"status": "ERR", "error_code": message.data[1]}
        return {"status": "UNKNOWN_PID"}

    def _build_cro(self, data: list) -> can.Message:
        return can.Message(
            arbitration_id=self.target_node_id,
            data=data,
            is_extended_id=False
        )
