import socket
import os
import threading
from concurrent.futures import ThreadPoolExecutor

def main():
    connected = 0
    # server_ip = input("Enter the server's IP address: ")
    server_ip = "10.0.4.10"
    server_port = 8888  # You can change the port if needed

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect((server_ip, server_port))
        print(f"Connected to {server_ip}:{server_port}")

        while True:
            # send client's ip address to server
            # message = client.getsockname()[0]
            if connected == 0:
                message = firstConnection()
                client.send(message.encode())
                response = client.recv(1024)
                print(f"Server Response: {response.decode()}")
                connected = 1
            else:
                message = input("Enter a message to send to the server: ")
                client.send(message.encode())
                response = client.recv(1024)
                print(f"Server Response: {response.decode()}")

    except ConnectionRefusedError:
        print("Failed to connect to the server. Make sure the server is running and check the IP and port.")

def firstConnection():
    type = 1
    flag = False
    latency = 500
    loss = 0
    # data is going to be a list of blocks of files
    data = ["tmp.txt", "tmp2.txt"]
    message = f"{type}, {flag}, {latency}, {loss}, {data}"
    return message

def save_blocks_to_files(file_path, block_size):
    try:
        with open(file_path, 'rb') as file:
            block_number = 0
            while True:
                data = file.read(block_size)
                if not data:
                    break
                block_number += 1
                # Save the block to a separate file
                block_filename = f"block_{block_number}.bin"  # Naming each block file
                with open(block_filename, 'wb') as block_file:
                    block_file.write(data)
                print(f"Block {block_number} saved to {block_filename}")
    except FileNotFoundError:
        print("File not found.")
    except Exception as e:
        print(f"Error: {e}")

def save_folder_into_blocks(file_path, block_size):
    for file in os.listdir(file_path):
        save_blocks_to_files(file_path + "/" + file, block_size = block_size)

# Example usage:
# send_file_via_udp('file_to_send.txt', '127.0.0.1', 12345)
# Replace 'file_to_send.txt' with the path to your file
# Replace '127.0.0.1' with the recipient's IP address
# Replace 12345 with the recipient's port number
def send_file_via_udp(file_path, host, port):
    # Create a UDP socket
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # Open the file to be sent
    try:
        with open(file_path, 'rb') as file:
            data = file.read()
            
            # Send the file in chunks over UDP
            udp_socket.sendto(data, (host, port))
            print(f"File '{file_path}' sent via UDP to {host}:{port}")
    except FileNotFoundError:
        print(f"File '{file_path}' not found.")
    finally:
        udp_socket.close()


# Example usage:
# receive_file_via_udp('received_file.txt', '127.0.0.1', 12345)
# Replace 'received_file.txt' with the path to save the received file
# Replace '127.0.0.1' with the local IP address or '0.0.0.0' to listen on all available interfaces
# Replace 12345 with the port number to listen on
def receive_file_via_udp(save_path, host, port):
    # Create a UDP socket
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # Bind the socket to the specified host and port
    udp_socket.bind((host, port))
    
    # Buffer size for receiving data
    buffer_size = 1024
    
    try:
        with open(save_path, 'wb') as file:
            print(f"Listening for incoming file at {host}:{port}")
            while True:
                # Receive data in chunks
                data, addr = udp_socket.recvfrom(buffer_size)
                if not data:
                    break
                
                # Write received data to the file
                file.write(data)
            
            print(f"File received and saved as '{save_path}'")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        udp_socket.close()

def concurrent_communication(tcp_server_address, udp_server_address, tcp_message, udp_files):
    with ThreadPoolExecutor(max_workers=2) as executor:
        executor.submit(tcp_client, tcp_server_address, tcp_message)
        executor.submit(receive_file_via_udp, udp_server_address, udp_files)

if __name__ == "__main__":
    main()
