import time
import can
import threading
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("MockECU")

class MockECU:
    def __init__(self, channel='test_channel', interface='virtual'):
        self.bus = can.Bus(channel=channel, interface=interface)
        self.running = False
        self.thread = None
        
        # Vehicle Signals
        self.speed = 0 # km/h (0-250)
        self.rpm = 800 # 0-8000
        
        # Network Management (NM) State
        self.nm_state = 'NORMAL' # NORMAL or SLEEP
        
    def start(self):
        logger.info("Starting ECU on Virtual CAN Bus...")
        self.running = True
        
        # Start main transmission thread
        self.thread = threading.Thread(target=self._run)
        self.thread.start()
        
        # Start NM listener thread
        self.nm_thread = threading.Thread(target=self._nm_listener)
        self.nm_thread.start()
        
    def stop(self):
        logger.info("Stopping ECU...")
        self.running = False
        if self.thread:
            self.thread.join()
        if self.nm_thread:
            self.nm_thread.join()
        self.bus.shutdown()
        
    def _nm_listener(self):
        """ Listens for Network Management commands (0x600 Go-To-Sleep) """
        while self.running:
            try:
                msg = self.bus.recv(timeout=0.1)
                if msg and msg.arbitration_id == 0x600:
                    if msg.data[0] == 0x00: # Sleep Command
                        logger.info("Received Go-To-Sleep command. Entering SLEEP mode.")
                        self.nm_state = 'SLEEP'
                    elif msg.data[0] == 0x01: # Wake Command
                        logger.info("Received Wakeup command. Entering NORMAL mode.")
                        self.nm_state = 'NORMAL'
            except can.CanError:
                pass
        
    def _run(self):
        """
        Main run loop broadcasting CAN messages.
        REQ-001: 0x100 (Engine Status) sent every 20ms
        """
        next_send_time = time.time()
        while self.running:
            if self.nm_state != 'SLEEP':
                # Boundary protections (Out of Range handling)
                safe_speed = max(0, min(int(self.speed), 250))
                safe_rpm = max(0, min(int(self.rpm), 8000))
                
                # Package Data
                # Byte 0: Speed 
                # Byte 1, 2: RPM (Big Endian)
                # Bytes 3-6: Padding / Reserved
                # Byte 7: Simple XOR Checksum of first 7 bytes
                data = bytearray([
                    safe_speed & 0xFF,
                    (safe_rpm >> 8) & 0xFF,
                    safe_rpm & 0xFF,
                    0, 0, 0, 0, 0
                ])
                
                # Calculate simple checksum
                checksum = 0
                for i in range(7):
                    checksum ^= data[i]
                data[7] = checksum
                
                msg = can.Message(
                    arbitration_id=0x100, 
                    data=data, 
                    is_extended_id=False
                )
                
                try:
                    self.bus.send(msg)
                except can.CanError as e:
                    logger.error(f"Failed to send 0x100: {e}")
            
            # Precise timing control for 20ms (+/- thread jitter) applies whether sleeping or not to keep the beat sync
            next_send_time += 0.020 
            sleep_time = next_send_time - time.time()
            if sleep_time > 0:
                time.sleep(sleep_time)

if __name__ == "__main__":
    ecu = MockECU()
    ecu.start()
    try:
        while True:
            time.sleep(1)
            # Simulated Ramp-Up sequence
            ecu.speed = min(ecu.speed + 5, 120)
            ecu.rpm = min(ecu.rpm + 200, 4500)
            logger.info(f"Simulating: Speed={ecu.speed} km/h, RPM={ecu.rpm}")
    except KeyboardInterrupt:
        ecu.stop()
