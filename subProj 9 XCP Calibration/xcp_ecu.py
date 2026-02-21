import struct
import can

class XcpError:
    ERR_CMD_IGNORED = 0x22
    ERR_ACCESS_DENIED = 0x24
    ERR_OUT_OF_RANGE = 0x23

class XcpSlaveNode:
    """
    Simulates a subordinate ECU containing internal hexadecimal memory addresses 
    that can be flashed or read over an XCP/CAN connection.
    """
    def __init__(self, node_id: int):
        self.node_id = node_id
        
        # Internal Memory Map (Address -> 4-byte Value)
        self.memory = {
            0x1000: bytearray(struct.pack("<I", 120)), # Speed Limit (120 km/h)
            0x1004: bytearray(struct.pack("<I", 850)), # AEB Braking Gain
            0x1008: bytearray(struct.pack("<I", 5000)) # Max RPM Limit
        }
        
        self.is_connected = False
        self.mta = 0x00000000 # Memory Transfer Address pointer

    def process_cro(self, message: can.Message) -> can.Message:
        """Processes a Command Receive Object (CRO) and returns a Data Transmission Object (DTO)."""
        pid = message.data[0]
        
        # 0xFF: CONNECT
        if pid == 0xFF:
            self.is_connected = True
            return self._build_dto(0xFF, [0x00]) # Positive Response (RES)

        # If not connected, reject all other commands
        if not self.is_connected:
            return self._build_dto(0xFE, [XcpError.ERR_CMD_IGNORED]) # Error (ERR)

        # 0xFE: DISCONNECT
        if pid == 0xFE:
            self.is_connected = False
            return self._build_dto(0xFF, [0x00])

        # 0xF6: SET_MTA (Set Memory Transfer Address)
        if pid == 0xF6:
            # Data: PID, Reserved, Reserved, Reserved, Addr[0], Addr[1], Addr[2], Addr[3]
            addr_bytes = bytes(message.data[4:8])
            self.mta = struct.unpack(">I", addr_bytes)[0] # Big-endian or Little-endian? Let's assume Big.
            
            if self.mta not in self.memory:
                return self._build_dto(0xFE, [XcpError.ERR_OUT_OF_RANGE])
                
            return self._build_dto(0xFF, [0x00])

        # 0xF5: UPLOAD (Read from MTA)
        if pid == 0xF5:
            num_elements = message.data[1]
            if self.mta not in self.memory:
                return self._build_dto(0xFE, [XcpError.ERR_OUT_OF_RANGE])
                
            data_out = list(self.memory[self.mta])
            # Auto-increment MTA (Not strictly implementing full MTA bounds for simplicity)
            return self._build_dto(0xFF, data_out)

        # 0xF0: DOWNLOAD (Write to MTA)
        if pid == 0xF0:
            num_elements = message.data[1]
            if self.mta not in self.memory:
                return self._build_dto(0xFE, [XcpError.ERR_OUT_OF_RANGE])
                
            # Extract the payload to write
            write_data = message.data[2 : 2 + num_elements]
            self.memory[self.mta] = bytearray(write_data)
            return self._build_dto(0xFF, [0x00])

        # Unknown Command
        return self._build_dto(0xFE, [XcpError.ERR_CMD_IGNORED])

    def _build_dto(self, pid: int, payload: list) -> can.Message:
        data = [pid] + payload
        # Pad to 8 bytes if needed
        while len(data) < 8:
            data.append(0x00)
            
        return can.Message(
            arbitration_id=self.node_id + 1, # Rx is node_id+1
            data=data[:8],
            is_extended_id=False
        )
