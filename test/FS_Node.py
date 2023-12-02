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

    def connect_to_tracker(self):
        tracker_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            tracker_socket.connect(self.tracker_address)
            print("Connected to FS_Tracker.")
            return tracker_socket
        except ConnectionRefusedError:
            print("Connection to FS_Tracker failed.")
            return None

    def register_and_update_files(self, tracker_socket, flag):
        if tracker_socket:
            try:
                data = {'node_ip': self.node_ip, 'files': self.shared_files, 'flag': flag}
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

    def download_file(self, file_name, file_locations, file_size):
        node_udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        file_content = b""
        if file_locations is None:
            print("File not found.")
            return
        # threads = []
        #for n in range(8)
        for node_address in file_locations:
            try:
                ic("Gonna ask for the file")
                node_udp_socket.sendto(file_name.encode(), (node_address[0], self.node_udp_port))
                ic("Now waiting for the file")
                # receive data while there is data to receive
                data, addr = node_udp_socket.recvfrom(file_size)  # Assuming a max data size of 4096 bytes
                ic("Received data")
                file_content += data
            except Exception as e:
                print(f"Failed to download file from {node_address}: {e}")
        ic(file_content)
        # make file_content the actual file content
        file_content = file_content.decode()
        # now save the file content to the shared folder with the file name
        file_path = os.path.join(self.shared_folder, file_name)
        with open(file_path, 'w') as file:
            file.write(file_content)
        # also add the file to the shared_files dict
        self.shared_files[file_name] = {'content': 'full', 'size': os.path.getsize(file_path)}
        print(f"Downloaded {file_name} successfully.")
        ic(self.shared_files)

    '''def send_file(self):
        node_udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        node_udp_socket.bind((self.node_ip, self.node_udp_port))

        while True:
            try:
                data, addr = node_udp_socket.recvfrom(4096)
                file_name = data.decode()

                # Assuming the file content is retrieved from self.shared_files
                file_content = self.shared_files.get(file_name)
                node_udp_socket.sendto(file_content.encode(), addr)
            except Exception as e:
                print(f"Failed to send file: {e}")'''

    def start_node(self, tracker_socket):
        udp_thread_send = threading.Thread(target=self.handle_udp_requests_2)
        udp_thread_send.start()
        ic(self.files_blocks)
        if tracker_socket:
            self.register_and_update_files(tracker_socket, 1)
            while True:
                file_name = input("Enter file name to download: ")
                # self.request_file(file_name, tracker_socket)
                file_locations, file_size = self.get_file_locations(file_name, tracker_socket)
                ic(file_locations)
                udp_thread_get = threading.Thread(target=self.download_file_3, args=(file_name, file_locations, file_size,))
                udp_thread_get.start()
                self.register_and_update_files(tracker_socket, 4)
                # now tell the tracker that you have the file

    def handle_udp_requests(self):
        node_udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # ip = input("Enter the IP address of the node: ")
        node_udp_socket.bind((self.node_ip, self.node_udp_port))

        while True:
            try:
                data, addr = node_udp_socket.recvfrom(4096)
                file_name = data.decode()

                # Process UDP request for file and send file content
                #file_content = self.shared_files.get(file_name, b"File not found")
                # make file_content the actual file content
                file_content = self.read_file(file_name)
                node_udp_socket.sendto(file_content.encode(), addr)
            except Exception as e:
                ic(f"Failed to handle UDP request: {e}")

    def get_file_locations(self, file_name, tracker_socket):
        if tracker_socket:
            try:
                data = {'file_name': file_name, 'flag': 2}
                serialized_data = pickle.dumps(data)
                tracker_socket.send(serialized_data)
                file_locations_data = tracker_socket.recv(4096)
                file_locations, file_size = pickle.loads(file_locations_data)
                print(f"Locations of {file_name}: {file_locations}")
                return file_locations, file_size
            except Exception as e:
                print(f"Failed to get file locations: {e}")
        else:
            print("No connection to FS_Tracker.")

    # probably not finished but it's a start


    def read_file(self, file_name):
        try:
            file_path = os.path.join(self.shared_folder, file_name)
            with open(file_path, 'r') as file:
                contents = file.read()
                return contents
        except FileNotFoundError:
            return "File not found"
        except Exception as e:
            return f"An error occurred: {str(e)}"


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
        # return {path.basename(file_path): file_blocks}
        self.files_blocks[path.basename(file_path)] = file_blocks

        '''
        def download_file_2(self, file_name, file_locations, file_size):
            file_size = int(file_size/7)

            node_udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            reconstructed_file = b""

            block_data = {}

            block_list = [1, 2, 3, 4, 5, 6, 7, 8]
            blocks_asked = []
            while len(block_list) > 0:
                for block_number, node_address in enumerate(file_locations, start=1):
                    try:
                        while block_number in blocks_asked:
                            block_number += 1
                        if block_number not in block_list:
                            continue
                        # block_info = file_blocks.get(block_number)
                        # if not block_info:
                        #     print(f"Block {block_number} not found for {file_name}")
                        #     continue
                        blocks_asked.append(block_number)
                        node_udp_socket.sendto(f"{file_name}:{block_number}".encode(), (node_address[0], self.node_udp_port))
                        data, addr = node_udp_socket.recvfrom(file_size)  # Assuming a max data size of 32768 bytes
                        block_list.remove(block_number)  # Remove block from list of blocks to be downloaded
                        # Collect received blocks
                        block_data[block_number] = data
                    except Exception as e:
                        print(f"Failed to download block {block_number} from {node_address}: {e}")
            # join all blocks in order from block_data
            for block_number in range(1, len(block_data) + 1):
                reconstructed_file += block_data[block_number]

            # Reconstruct the file from received blocks
            file_path = os.path.join(self.shared_folder, file_name)
            with open(file_path, 'wb') as file:
                file.write(reconstructed_file)

            print(f"Downloaded {file_name} successfully.")
        '''

    def download_file_3(self, file_name, file_locations, file_size):
        file_size = int(file_size / 7)

        node_udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        reconstructed_file = b""
        block_data = {}
        block_list = [1, 2, 3, 4, 5, 6, 7, 8]
        lock = threading.Lock()  # Create a lock for thread synchronization

        def download_block(block_number, node_address):
            nonlocal block_data
            try:
                node_udp_socket.sendto(f"{file_name}:{block_number}".encode(), (node_address[0], self.node_udp_port))
                data, addr = node_udp_socket.recvfrom(file_size)  
                with lock:  # Acquire lock before accessing shared resources
                    block_data[block_number] = data
            except Exception as e:
                print(f"Failed to download block {block_number} from {node_address}: {e}")

        # Create threads for downloading blocks concurrently
        threads = []
        blocks_requested = set()  # Maintain a set of blocks already requested

        for block_number in block_list:
            for node_address in file_locations:
                # Check if the block has already been requested
                if block_number not in blocks_requested:
                    blocks_requested.add(block_number)
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

        print(f"Downloaded {file_name} successfully.")

    def handle_udp_requests_2(self):
        node_udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # ip = input("Enter the IP address of the node: ")
        node_udp_socket.bind((self.node_ip, self.node_udp_port))

        while True:
            try:
                data, addr = node_udp_socket.recvfrom(4096)
                file_name_and_block = data.decode()

                # Process UDP request for file and send file content
                file_content = self.read_file_2(file_name_and_block)
                node_udp_socket.sendto(file_content, addr)
            except Exception as e:
                ic(f"Failed to handle UDP request: {e}")

    def read_file_2(self, file_block):
        # got to self.files_blocks and get the file_block
        file_name, block_number = file_block.split(":")
        file_blocks = self.files_blocks[file_name]
        block_info = file_blocks.get(int(block_number))
        if not block_info:
            print(f"Block {block_number} not found for {file_name}")
            return
        return block_info['data']