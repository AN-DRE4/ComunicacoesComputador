import socket
import threading
import pickle  # For serialization
from icecream import ic

class FS_Tracker:
    def __init__(self):
        self.node_registry = {}  # {node_ip: {address, files}}
        self.tracker_address = ('10.0.0.10', 5000)  # Tracker's address

    def start_tracker(self):
        tracker_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tracker_socket.bind(self.tracker_address)
        tracker_socket.listen(5)
        ic("FS_Tracker started. Waiting for connections...")
        '''test'''

        # conn, addr = tracker_socket.accept()
        # ic(f"Connected to node at {addr}")

        '''test'''

        while True:
            conn, addr = tracker_socket.accept()
            ic(f"Connected to node at {addr}")

            # Handle each node connection in a separate thread
            node_handler = threading.Thread(target=self.handle_node, args=(conn, addr,))
            node_handler.start()
            
    def handle_node(self, conn, addr):
        while True:
            data = conn.recv(4096)
            if data:
                serialized_data = pickle.loads(data)
                ic(f"Received data: {serialized_data}")
                if serialized_data['flag'] == 1:
                    self.register_node(conn.getpeername()[0], addr, serialized_data['files'])
                if serialized_data['flag'] == 4:
                    self.node_registry[conn.getpeername()[0]]['files'].update(serialized_data['files'])
                file_name = serialized_data.get('file_name')
                ic(f"Received file name: {file_name}")
                if file_name:
                    file_locations = self.get_file_locations(file_name)
                    serialized_locations = pickle.dumps(file_locations)
                    conn.send(serialized_locations)
            # print all files in the registry
            ic("Node Registry:")
            for node_ip, node_info in self.node_registry.items():
                ic(f"Node {node_ip}: {node_info['address']}, {node_info['files']}")
            # conn.close()

    def register_node(self, node_ip, address, files):
        self.node_registry[node_ip] = {'address': address, 'files': files}

    def get_file_locations(self, file_name):
        file_locations = []
        for node_ip, node_info in self.node_registry.items():
            if file_name in node_info['files']:
                file_locations.append(node_info['address'])
        return file_locations

    def node_inactive(self, node_ip):
        if node_ip in self.node_registry:
            del self.node_registry[node_ip]

    '''def handle_file_request(self):
        tracker_udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        tracker_udp_socket.bind(self.tracker_address)

        while True:
            try:
                data, addr = tracker_udp_socket.recvfrom(4096)
                file_name = data.decode()
                file_locations = self.get_file_locations(file_name)
                serialized_locations = pickle.dumps(file_locations)
                tracker_udp_socket.sendto(serialized_locations, addr)
            except Exception as e:
                ic(f"Failed to handle file request: {e}")'''

