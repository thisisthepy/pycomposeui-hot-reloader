import socket
import threading
import json
from src.main.server.observer import start_monitoring


def handle_client(client_socket, address):
    """Handles communication with a client."""
    try:
        print(f'New connection from {address}')
        while True:
            data = client_socket.recv(1024)
            if not data:
                print(f'Client {address} disconnected')
                break
            # Process received data here
            print(f'Received data from {address}: {data.decode()}')
    except Exception as e:
        print(f'Error handling client {address}: {e}')
    finally:
        client_socket.close()


def send_file_change_info(current_event, socket_connections: dict):
    """Sends file change information to clients via TCP socket."""
    message = json.dumps(current_event)
    if socket_connections:
        for client_socket in list(socket_connections.values()).copy():
            try:
                client_socket['socket'].send(message.encode())
                print(f'The event {current_event} was sent to ({len(socket_connections)}) client(s).')
            except Exception as e:
                print(f'Error sending message to client: {e}')


def set_up_server():
    # Set up server socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('127.0.0.1', 8000))
    server_socket.listen()

    socket_connections = {}  # Dictionary to store client connections

    try:
        while True:
            client_socket, address = server_socket.accept()
            # Create a new thread to handle each client
            client_thread = threading.Thread(target=handle_client, args=(client_socket, address))
            client_thread.start()
            socket_connections[address] = {'socket': client_socket, 'information_sent': False}
    except KeyboardInterrupt:
        print("Server shutting down...")
    finally:
        server_socket.close()
