import socket
import os
import threading
from icecream import ic  # For debugging
import pickle  # For serialization
from os import path

class FS_Node:
    def __init__(self, node_ip, shared_files, shared_folder):
        self.node_ip = node_ip
        self.shared_folder = shared_folder
        self.shared_files = shared_files  # {file_name: {blocks} or 'full'}
        self.files_blocks = {}  # {file_name: {blocks}}
        self.tracker_address = ('10.0.0.10', 5000)  # Assume tracker is running locally
        self.node_udp_port = 8888  # Node's UDP port for file transfer
        self.tracker_socket = None

    def connect_to_tracker(self):
        tracker_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            tracker_socket.connect(self.tracker_address)
            print("Connected to FS_Tracker.")
            self.tracker_socket = tracker_socket
            return tracker_socket
        except ConnectionRefusedError:
            print("Connection to FS_Tracker failed.")
            return None

    def register_and_update_files(self, flag):
        if self.tracker_socket:
            try:
                data = {'node_ip': self.node_ip, 'files': self.shared_files, 'flag': flag}
                serialized_data = pickle.dumps(data)
                self.tracker_socket.send(serialized_data)
                print("Files registered with FS_Tracker.")
            except Exception as e:
                print(f"Failed to register files: {e}")
        else:
            print("No connection to FS_Tracker.")

    def start_node(self):
        udp_thread_send = threading.Thread(target=self.handle_udp_requests_2)
        udp_thread_send.start()
        ic(self.files_blocks)
        if self.tracker_socket:
            self.register_and_update_files(1)
            while True:
                file_name = input("Enter file name to download: ")
                file_locations, file_size = self.get_file_locations(file_name)
                ic(file_locations)
                udp_thread_get = threading.Thread(target=self.download_file_3, args=(file_name, file_locations, file_size,))
                udp_thread_get.start()

    def get_file_locations(self, file_name):
        if self.tracker_socket:
            try:
                data = {'file_name': file_name, 'flag': 2}
                serialized_data = pickle.dumps(data)
                self.tracker_socket.send(serialized_data)
                file_locations_data = self.tracker_socket.recv(4096)
                file_locations, file_size = pickle.loads(file_locations_data)
                print(f"Locations of {file_name}: {file_locations}")
                return file_locations, file_size
            except Exception as e:
                print(f"Failed to get file locations: {e}")
        else:
            print("No connection to FS_Tracker.")

    def create_file_blocks_dict(self, file_path, block_size):
        file_blocks = {}
        with open(file_path, 'rb') as file:
            block_number = 1
            while True:
                block = file.read(block_size)
                if not block:
                    break
                file_blocks[block_number] = {
                    'data': block,
                    'block_size': len(block)
                }
                block_number += 1
        file_info = {
            'number_of_blocks': len(file_blocks)
        }
        file_blocks['__file_info__'] = file_info
        self.files_blocks[path.basename(file_path)] = file_blocks

    def download_file_3(self, file_name, file_locations, file_size):
        file_size = int(file_size / 7)

        node_udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        reconstructed_file = b""
        block_data = {}
        block_list = [1, 2, 3, 4, 5, 6, 7, 8]
        lock = threading.Lock()  # Create a lock for thread synchronization

        blocks_per_node = len(block_list) // len(file_locations)  # Calculate number of blocks per node
        blocks_assigned = {node_address: block_list[i*blocks_per_node:(i+1)*blocks_per_node] for i, node_address in enumerate(file_locations)}

        def download_block(block_number, node_address):
            nonlocal block_data
            if block_number in blocks_assigned[node_address]:
                try:
                    node_udp_socket.sendto(f"{file_name}:{block_number}".encode(), (node_address[0], self.node_udp_port))
                    data, addr = node_udp_socket.recvfrom(file_size)  
                    with lock:  # Acquire lock before accessing shared resources
                        block_data[block_number] = data
                except Exception as e:
                    print(f"Failed to download block {block_number} from {node_address}: {e}")

        # Create threads for downloading blocks concurrently
        threads = []

        for block_number in block_list:
            for node_address in file_locations:
                thread = threading.Thread(target=download_block, args=(block_number, node_address))
                threads.append(thread)
                thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Join all blocks in order from block_data
        for block_number in range(1, len(block_data) + 1):
            ic(block_number, block_data[block_number].decode())
            reconstructed_file += block_data[block_number]

        # Reconstruct the file from received blocks
        file_path = os.path.join(self.shared_folder, file_name)
        with open(file_path, 'wb') as file:
            file.write(reconstructed_file)

        # add the file to the shared files dict
        self.shared_files[file_name] = {'content': 'full', 'size': os.path.getsize(file_path)}
        self.create_file_blocks_dict(file_path, file_size)
        self.register_and_update_files(4)

        print(f"Downloaded {file_name} successfully.")

    def handle_udp_requests_2(self):
        node_udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        node_udp_socket.bind((self.node_ip, self.node_udp_port))

        while True:
            try:
                data, addr = node_udp_socket.recvfrom(4096)
                file_name_and_block = data.decode()

                # Process UDP request for file and send file content
                file_content = self.read_file(file_name_and_block)
                node_udp_socket.sendto(file_content, addr)
            except Exception as e:
                ic(f"Failed to handle UDP request: {e}")

    def read_file(self, file_block):
        # got to self.files_blocks and get the file_block
        file_name, block_number = file_block.split(":")
        file_blocks = self.files_blocks[file_name]
        block_info = file_blocks.get(int(block_number))
        if not block_info:
            print(f"Block {block_number} not found for {file_name}")
            return
        return block_info['data']