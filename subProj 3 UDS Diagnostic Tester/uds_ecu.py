import time
import logging
import threading
import can
import isotp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("UDS_ECU")

class MockUDSECU:
    def __init__(self, channel='test_uds_bus', interface='virtual'):
        self.bus = can.Bus(channel=channel, interface=interface)
        
        # 11-bit Normal Addressing: Tester = 0x7E0, ECU = 0x7E8
        self.addr = isotp.Address(isotp.AddressingMode.Normal_11bits, rxid=0x7E0, txid=0x7E8)
        self.stack = isotp.CanStack(self.bus, address=self.addr, error_handler=self._isotp_error)
        
        self.running = False
        self.thread = None
        
        # State variables
        self.current_session = 0x01 # Default Session
        self.seed_requested = False
        self.security_unlocked = False
        
        self.VIN = b"WBA00000000000000"

    def _isotp_error(self, error):
        logger.warning(f"ISO-TP Error: {error}")

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        logger.info("Mock UDS ECU Started.")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        self.bus.shutdown()
        logger.info("Mock UDS ECU Stopped.")

    def _run(self):
        while self.running:
            self.stack.process()
            
            if self.stack.available():
                payload = self.stack.recv()
                if payload:
                    response = self.process_request(bytearray(payload))
                    if response:
                        self.stack.send(response)
                        
            # Prevent 100% CPU utilization
            time.sleep(0.005)

    def process_request(self, payload):
        """
        Parses the raw UDS payload and returns the appropriate ISO 14229 response.
        If the payload is invalid, it returns a Negative Response Code (NRC) array:
        [0x7F, SID, NRC]
        """
        if len(payload) == 0:
            return None
            
        sid = payload[0]
        
        # 0x10 - Diagnostic Session Control
        if sid == 0x10:
            if len(payload) != 2:
                return bytearray([0x7F, 0x10, 0x13]) # Incorrect Message Length
                
            sub_function = payload[1]
            if sub_function in [0x01, 0x02, 0x03]:
                self.current_session = sub_function
                return bytearray([0x50, sub_function, 0x00, 0x32, 0x01, 0xF4]) # Positive Response with dummy timing params
            else:
                return bytearray([0x7F, 0x10, 0x12]) # Sub-function Not Supported

        # 0x22 - Read Data By Identifier
        elif sid == 0x22:
            if len(payload) != 3:
                return bytearray([0x7F, 0x22, 0x13]) # Incorrect Message Length
                
            did = (payload[1] << 8) | payload[2]
            if did == 0xF190: # VIN
                resp = bytearray([0x62, 0xF1, 0x90])
                resp.extend(self.VIN)
                return resp
            else:
                return bytearray([0x7F, 0x22, 0x31]) # Request Out of Range
                
        # 0x27 - Security Access
        elif sid == 0x27:
            if len(payload) < 2:
                return bytearray([0x7F, 0x27, 0x13]) # Incorrect Message Length
                
            sub_function = payload[1]
            
            if sub_function == 0x01: # Request Seed
                if len(payload) != 2:
                    return bytearray([0x7F, 0x27, 0x13])
                self.seed_requested = True
                # Constant seed for testing
                return bytearray([0x67, 0x01, 0xAA, 0xBB, 0xCC, 0xDD]) 
                
            elif sub_function == 0x02: # Send Key
                if not self.seed_requested:
                    return bytearray([0x7F, 0x27, 0x24]) # Request Sequence Error
                if len(payload) != 6:
                    return bytearray([0x7F, 0x27, 0x13])
                    
                # Dummy logic: Key is just bits inverted of Seed (which is AA BB CC DD)
                # Invert AA->55, BB->44, CC->33, DD->22
                key_provided = payload[2:]
                expected_key = bytearray([0x55, 0x44, 0x33, 0x22])
                
                if key_provided == expected_key:
                    self.security_unlocked = True
                    self.seed_requested = False
                    return bytearray([0x67, 0x02]) # Positive Response
                else:
                    self.seed_requested = False # State reset on failure
                    return bytearray([0x7F, 0x27, 0x33]) # Security Access Denied
            else:
                return bytearray([0x7F, 0x27, 0x12]) # Sub-function Not Supported

        # Unknown SID
        else:
            return bytearray([0x7F, sid, 0x11]) # Service Not Supported

if __name__ == "__main__":
    ecu = MockUDSECU()
    ecu.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        ecu.stop()
