from icecream import ic
import socket
import threading

class FS_Tracker_Header():
    '''
        Type 1: First connection
        Type 2: Asking for file
        Type 3: Never got the file
    '''
    def __init__(self):
        ip = 0
        type = 0
        flag = True
        network_condition = 0
        latency_time = 0
        data = list()

class FS_Tracker_Protocol():
    # create a dictionary with the client ip as key and the list header as value
    def __init__(self):
        self.dicionario = {}
        


def read_file_to_list(file_path):
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
            # Strip trailing newline characters from each line and create a list of strings
            lines = [line.strip() for line in lines]
        return lines
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return []
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return []
    
def create_dict(lines):
    config_dict = {}
    for line in lines:
        # Split the line into key and value
        key, value = line.split(",")[0], line.split(",")[1:]
        # Strip leading and trailing whitespace from both key and value
        key = key.strip()
        # Add the key-value pair to the dictionary
        config_dict[key] = value
    return config_dict

'''def sendNeighbours(dic, client_ip):
    for key, value in dic.items():
        if key == client_ip:
            # make the value a string
            value = str(value)
            # remove the square brackets
            value = value.replace("[", "")
            value = value.replace("]", "")
            # remove the single quotes
            value = value.replace("'", "")
            return value'''

def createHeader(ip, data):
    header = FS_Tracker_Header()
    header.ip = ip
    header.type = data[0]
    header.flag = data[1]
    header.network_condition = data[2]
    header.latency_time = data[3]
    header.data = data[4:]
    return header

def handle_client(client_socket):
    while True:
        data = client_socket.recv(1024)
        if not data:
            break
        ic(f"Received: {data.decode().split(',')}")
        if data.decode().split(',')[0] == "1":
            header = createHeader(client_socket.getpeername()[0], data.decode().split(","))
            # print all elements of the header
            ic(header.ip)
            ic(header.type)
            ic(header.flag)
            ic(header.network_condition)
            ic(header.latency_time)
            ic(header.data)
            message = "Message received"
            client_socket.send(message.encode())
        elif data.decode().split(',')[0] == "2":
            message = "Message received 2"
            client_socket.send(message.encode())

def connectToClient():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", 8888))
    server.listen(5)
    print("Server listening on port 8888")
    #print server's ip
    #ic(f"Server's IP address: {socket.gethostbyname(socket.gethostname())}")

    while True:
        client_socket, addr = server.accept()
        print(f"Accepted connection from {addr[0]}:{addr[1]}")
        client_handler = threading.Thread(target=handle_client, args=(client_socket, ))
        client_handler.start()


def main():
    tracker = FS_Tracker_Protocol()
    connectToClient()


if __name__ == "__main__":
    main()

