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
                if serialized_data['flag'] == 2:
                    ic(f"Received file name: {file_name}")
                    file_locations = self.get_file_locations(file_name)
                    serialized_locations = pickle.dumps(file_locations)
                    conn.send(serialized_locations)
                if serialized_data['flag'] != 2:
                    ic(serialized_data['flag'])
                    ic("Node Registry:")
                    for node_ip, node_info in self.node_registry.items():
                        ic(node_ip, node_info['address'], node_info['files'])

    def register_node(self, node_ip, address, files):
        self.node_registry[node_ip] = {'address': address, 'files': files}

    def get_file_locations(self, file_name):
        file_locations = []
        file_size = None
        for node_ip, node_info in self.node_registry.items():
            if file_name in node_info['files']:
                if file_size is None:
                    file_size = node_info['files'][file_name]['size']
                file_locations.append(node_info['address'])
        # return the file locations and the file size
        return file_locations, file_size

    def node_inactive(self, node_ip):
        if node_ip in self.node_registry:
            del self.node_registry[node_ip]
            