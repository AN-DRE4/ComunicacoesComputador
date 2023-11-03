import socket

def main():
    connected = 0
    # server_ip = input("Enter the server's IP address: ")
    server_ip = "10.0.0.10"
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

if __name__ == "__main__":
    main()
