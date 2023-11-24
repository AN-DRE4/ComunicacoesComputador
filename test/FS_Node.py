import socket
import threading
from icecream import ic  # For debugging
import pickle  # For serialization

class FS_Node:
    def __init__(self, node_id, shared_folder):
        self.node_id = node_id
        self.shared_folder = shared_folder  # {file_name: [blocks]}
        self.tracker_address = ('10.0.1.10', 5000)  # Assume tracker is running locally
        self.node_udp_port = 8888  # Node's UDP port for file transfer

    def connect_to_tracker(self):
        tracker_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            tracker_socket.connect(self.tracker_address)
            print("Connected to FS_Tracker.")
            return tracker_socket
        except ConnectionRefusedError:
            print("Connection to FS_Tracker failed.")
            return None

    def register_files(self, tracker_socket):
        if tracker_socket:
            try:
                data = {'node_id': self.node_id, 'files': self.shared_folder, 'flag': 1}
                serialized_data = pickle.dumps(data)
                tracker_socket.send(serialized_data)
                print("Files registered with FS_Tracker.")
            except Exception as e:
                print(f"Failed to register files: {e}")
        else:
            print("No connection to FS_Tracker.")

    def request_file(self, file_name, tracker_socket):
        if tracker_socket:
            try:
                data = {'file_name': file_name, 'flag': 2}
                serialized_data = pickle.dumps(data)
                tracker_socket.send(serialized_data)
                print(f"Request sent to FS_Tracker for file: {file_name}")
            except Exception as e:
                print(f"Failed to request file: {e}")
        else:
            print("No connection to FS_Tracker.")

    def download_file(self, file_name, file_locations):
        node_udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        file_content = b""
        if file_locations is None:
            print("File not found.")
            return
        for node_address in file_locations:
            try:
                ic("Gonna ask for the file")
                node_udp_socket.sendto(file_name.encode())
                ic("Now waiting for the file")
                data, addr = node_udp_socket.recvfrom(4096)  # Assuming a max data size of 4096 bytes
                ic("Got the file")
                file_content += data
                ic(file_content)
            except Exception as e:
                print(f"Failed to download file from {node_address}: {e}")

        # Save the downloaded file content or process it further
        # Example: Save file to disk, reconstruct file content from blocks, etc.
        print(f"Downloaded {file_name} successfully.")

    def send_file(self):
        node_udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        node_udp_socket.bind(('10.0.1.10', self.node_udp_port))

        while True:
            try:
                data, addr = node_udp_socket.recvfrom(4096)
                file_name = data.decode()

                # Assuming the file content is retrieved from self.shared_folder
                file_content = self.shared_folder.get(file_name, b"File not found")
                node_udp_socket.sendto(file_content, addr)
            except Exception as e:
                print(f"Failed to send file: {e}")

    def start_node(self, tracker_socket):
        udp_thread_send = threading.Thread(target=self.handle_udp_requests)
        udp_thread_send.start()
        if tracker_socket:
            self.register_files(tracker_socket)
            while True:
                file_name = input("Enter file name to download: ")
                # self.request_file(file_name, tracker_socket)
                file_locations = self.get_file_locations(file_name, tracker_socket)
                udp_thread_get = threading.Thread(target=self.download_file, args=(file_name, file_locations,))
                udp_thread_get.start()
                # self.download_file(file_name, file_locations)

    def handle_udp_requests(self):
        node_udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        ip = input("Enter the IP address of the node: ")
        node_udp_socket.bind((ip, self.node_udp_port))

        while True:
            try:
                data, addr = node_udp_socket.recvfrom(4096)
                file_name = data.decode()

                # Process UDP request for file and send file content
                file_content = self.shared_folder.get(file_name, b"File not found")
                node_udp_socket.sendto(file_content, addr)
            except Exception as e:
                print(f"Failed to handle UDP request: {e}")

    def get_file_locations(self, file_name, tracker_socket):
        if tracker_socket:
            try:
                data = {'file_name': file_name, 'flag': 2}
                serialized_data = pickle.dumps(data)
                tracker_socket.send(serialized_data)
                file_locations_data = tracker_socket.recv(4096)
                file_locations = pickle.loads(file_locations_data)
                print(f"Locations of {file_name}: {file_locations}")
                return file_locations
            except Exception as e:
                print(f"Failed to get file locations: {e}")
        else:
            print("No connection to FS_Tracker.")

    # probably not finished but it's a start