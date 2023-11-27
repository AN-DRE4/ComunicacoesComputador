# File: node.py
import os

from FS_Node import FS_Node

# create dict of files from shared folder
def get_files(folder_name):
    files = {}
    for file in os.listdir(folder_name):
        if os.path.isfile(os.path.join(folder_name, file)):
            files[file] = file
    return files

if __name__ == "__main__":
    ip = input("Enter the IP address of the node: ")
    shared_folder = input("Enter the path to the shared folder: ")
    # tracker_ip = input("Enter the IP address of the tracker: ")
    files = get_files(shared_folder)
    print(files)
    node = FS_Node(node_ip=ip, shared_files=files, shared_folder=shared_folder)  # Provide a unique node_id
    tracker_socket = node.connect_to_tracker()

    if tracker_socket:
        # node.register_files(tracker_socket)
        node.start_node(tracker_socket)
    else:
        print("Failed to connect to FS_Tracker.")
