import socket
import struct
import threading
import time

# SOME/IP Constants
PROTOCOL_VERSION = 1
INTERFACE_VERSION = 1
MSG_TYPE_REQUEST = 0x00
MSG_TYPE_RESPONSE = 0x80
MSG_TYPE_NOTIFICATION = 0x02

SERVICE_ID = 0x1234
METHOD_SUBSCRIBE = 0x0001
METHOD_STOPSUBSCRIBE = 0x0002
EVENT_GPS = 0x8001
EVENTGROUP_ID = 0x0001

class SomeipServer:
    def __init__(self, host='127.0.0.1', port=30501, sd_port=30490):
        self.host = host
        self.port = port
        self.sd_port = sd_port
        
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Allow port reuse for testing
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))
        
        self.running = False
        self.subscribers = set()
        
        self.sd_thread = None
        self.listen_thread = None
        self.notify_thread = None

    def start(self):
        self.running = True
        self.sd_thread = threading.Thread(target=self._broadcast_sd, daemon=True)
        self.listen_thread = threading.Thread(target=self._listen, daemon=True)
        self.notify_thread = threading.Thread(target=self._publish_notifications, daemon=True)
        
        self.sd_thread.start()
        self.listen_thread.start()
        self.notify_thread.start()

    def stop(self):
        self.running = False
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass

    def _broadcast_sd(self):
        """Broadcasts OfferService (Service Discovery) to the designated SD port."""
        sd_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        while self.running:
            # Mock OfferService SD Packet
            msg_id = (0xFFFF << 16) | 0x8100 # SD Message ID
            req_id = 0x00000000
            
            # Payload: ServiceID, InstanceID, MajorVer, TTL
            payload = struct.pack("!HHBH", SERVICE_ID, 0x0001, 0x01, 0x05)
            length = 8 + len(payload)
            
            # Header: msg_id, length, req_id, proto_v, iface_v, msg_type, ret_code
            header = struct.pack("!IIIBBBB", msg_id, length, req_id, PROTOCOL_VERSION, INTERFACE_VERSION, MSG_TYPE_NOTIFICATION, 0x00)
            
            sd_sock.sendto(header + payload, (self.host, self.sd_port))
            time.sleep(0.5)
        sd_sock.close()

    def _listen(self):
        """Listens for SubscribeEventgroup requests."""
        while self.running:
            try:
                data, addr = self.sock.recvfrom(1024)
                if len(data) >= 16:
                    header = struct.unpack("!IIIBBBB", data[:16])
                    msg_id = header[0]
                    proto_v = header[3]
                    msg_type = header[5]
                    payload = data[16:]
                    
                    # Protocol Version Handshaking
                    if proto_v != PROTOCOL_VERSION:
                        continue # Silently drop malformed packets
                    
                    srv_id = (msg_id >> 16) & 0xFFFF
                    method_id = msg_id & 0xFFFF
                    
                    if srv_id == SERVICE_ID and msg_type == MSG_TYPE_REQUEST:
                        if method_id == METHOD_SUBSCRIBE:
                            # Extract eventgroup from payload
                            if len(payload) >= 2:
                                eg_id = struct.unpack("!H", payload[:2])[0]
                                if eg_id == EVENTGROUP_ID:
                                    self.subscribers.add(addr)
                                    self._send_subscribe_ack(addr, header[2]) # header[2] is request_id
                                    
                        elif method_id == METHOD_STOPSUBSCRIBE:
                            # Teardown sequence
                            if addr in self.subscribers:
                                self.subscribers.remove(addr)
                            self._send_subscribe_ack(addr, header[2], method=METHOD_STOPSUBSCRIBE)
            except Exception:
                pass
                
    def _send_subscribe_ack(self, addr, request_id, method=METHOD_SUBSCRIBE):
        """Sends a SubscribeEventgroupAck response."""
        msg_id = (SERVICE_ID << 16) | method
        payload = struct.pack("!H", EVENTGROUP_ID)
        length = 8 + len(payload)
        
        header = struct.pack("!IIIBBBB", msg_id, length, request_id, PROTOCOL_VERSION, INTERFACE_VERSION, MSG_TYPE_RESPONSE, 0x00) # 0x00 = E_OK
        self.sock.sendto(header + payload, addr)

    def _publish_notifications(self):
        """Publishes mock GPS float coordinates to all subscribers."""
        mock_lat = 45.1234
        while self.running:
            if self.subscribers:
                msg_id = (SERVICE_ID << 16) | EVENT_GPS
                payload = struct.pack("!f", mock_lat)
                length = 8 + len(payload)
                
                header = struct.pack("!IIIBBBB", msg_id, length, 0x00000000, PROTOCOL_VERSION, INTERFACE_VERSION, MSG_TYPE_NOTIFICATION, 0x00)
                
                for addr in list(self.subscribers):
                    try:
                        self.sock.sendto(header + payload, addr)
                    except Exception:
                        pass
                mock_lat += 0.0001
            time.sleep(0.1)

if __name__ == "__main__":
    server = SomeipServer()
    server.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        server.stop()
