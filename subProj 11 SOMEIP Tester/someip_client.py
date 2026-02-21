import socket
import struct
import time

PROTOCOL_VERSION = 1
INTERFACE_VERSION = 1
MSG_TYPE_REQUEST = 0x00
MSG_TYPE_RESPONSE = 0x80
MSG_TYPE_NOTIFICATION = 0x02

class SomeipClient:
    def __init__(self, host='127.0.0.1', sd_port=30490):
        self.host = host
        self.sd_port = sd_port
        
        # Socket for SD listening
        self.sd_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sd_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sd_sock.bind((self.host, self.sd_port))
        self.sd_sock.settimeout(2.0)
        
        # Socket for Application Data (Pub/Sub)
        self.app_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Bind app socket to a random open port
        self.app_sock.bind((self.host, 0))
        self.app_sock.settimeout(2.0)

    def wait_for_offer(self, target_service_id) -> bool:
        """Listens on the SD port for an OfferService matching the target_service_id."""
        end_time = time.time() + 5.0
        while time.time() < end_time:
            try:
                data, _ = self.sd_sock.recvfrom(1024)
                if len(data) >= 16:
                    header = struct.unpack("!IIIBBBB", data[:16])
                    payload = data[16:]
                    
                    if len(payload) >= 2:
                        # In our mock server, payload[0:2] is the Service ID
                        srv_id = struct.unpack("!H", payload[:2])[0]
                        if srv_id == target_service_id:
                            return True
            except socket.timeout:
                pass
        return False

    def subscribe_eventgroup(self, server_ip, server_port, service_id, eventgroup_id) -> bool:
        """Sends a SubscribeEventgroup Request and waits for the Response."""
        msg_id = (service_id << 16) | 0x0001 # 0x0001 is METHOD_SUBSCRIBE
        req_id = 0x01230001 # Client ID 0x0123, Session ID 1
        
        payload = struct.pack("!H", eventgroup_id)
        length = 8 + len(payload)
        
        header = struct.pack("!IIIBBBB", msg_id, length, req_id, PROTOCOL_VERSION, INTERFACE_VERSION, MSG_TYPE_REQUEST, 0x00)
        
        self.app_sock.sendto(header + payload, (server_ip, server_port))
        
        # Wait for SubscribeAck
        try:
            data, _ = self.app_sock.recvfrom(1024)
            if len(data) >= 16:
                resp_header = struct.unpack("!IIIBBBB", data[:16])
                if resp_header[5] == MSG_TYPE_RESPONSE and resp_header[6] == 0x00: # E_OK
                    return True
        except socket.timeout:
            pass
        return False

    def receive_notification(self, service_id, event_id):
        """Listens for a Notification message and parses the float payload."""
        try:
            data, _ = self.app_sock.recvfrom(1024)
            if len(data) >= 16:
                header = struct.unpack("!IIIBBBB", data[:16])
                msg_id = header[0]
                msg_type = header[5]
                
                srv_id = (msg_id >> 16) & 0xFFFF
                ev_id = msg_id & 0xFFFF
                
                if srv_id == service_id and ev_id == event_id and msg_type == MSG_TYPE_NOTIFICATION:
                    payload = data[16:]
                    if len(payload) == 4:
                        value = struct.unpack("!f", payload)[0]
                        return round(value, 4)
        except socket.timeout:
            pass
        return None

    def close(self):
        self.sd_sock.close()
        self.app_sock.close()
