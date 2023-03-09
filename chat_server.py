import socket
import sys
from threading import Thread, Lock


class ChatServer:
    def __init__(self, ip_addr=socket.gethostbyname(socket.gethostname()), port=2900):
        self.ip_addr = ip_addr
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients = {}
        self.lock = Lock()
        self.message_queue = {}
        self.running = False

    def start(self):
        self.running = True
        try:
            self.server_socket.bind((self.ip_addr, self.port))
        except socket.error as e:
            print(e)
            self.server_socket.close()
            sys.exit(1)
        self.server_socket.listen()
        self.server_socket.settimeout(1)
        print(f"Listening on {self.ip_addr}:{self.port}")
        try:
            while self.running:
                try:
                    client_socket, address = self.server_socket.accept()
                    client_thread = Thread(target=self.handle_client, args=(client_socket, address), daemon=True)
                    client_thread.start()
                except socket.timeout:
                    pass
        except KeyboardInterrupt:
            print("\nStopping server due to user request")
            self.running = False
        finally:
            self.stop()

    def stop(self):
        self.running = False
        for client_socket in self.clients.values():
            client_socket.close()
        self.server_socket.close()

    def handle_client(self, client_socket, address):
        client_id = client_socket.recv(1024).decode()

        with self.lock:
            if client_id in self.clients:
                client_socket.send(b"ERROR: Client ID already taken. Please choose another one.")
                return
            else:
                self.clients[client_id] = client_socket
                print(f"Client '{client_id}' connected from {address}\n")
                client_socket.send(b"SUCCESS")

        while True:
            try:
                message = client_socket.recv(1024).decode()
                if not message:
                    continue

                # Handle different message types
                parts = message.split(" ")
                command = parts[0]

                # Implement message routing to other clients and message queue
                if command == "SEND":
                    recipient = parts[1]
                    msg = " ".join(parts[2:])
                    if recipient not in self.clients:
                        client_socket.send(f"Error: No client with ID '{recipient}' found.\n".encode())
                    else:
                        with self.lock:
                            if recipient in self.message_queue:
                                self.message_queue[recipient].append((client_id, msg))
                            else:
                                self.message_queue[recipient] = [(client_id, msg)]
                        # self.clients[recipient].send(f"{client_id}: {msg}".encode())

                elif command == "LIST":
                    with self.lock:
                        other_clients = [cid for cid in self.clients if cid != client_id]
                        client_socket.sendall("\n".join(other_clients).encode())

                elif command == "CHECK":
                    with self.lock:
                        if client_id in self.message_queue:
                            for sender, msg in self.message_queue[client_id]:
                                client_socket.sendall(f"{sender} {msg}".encode())
                            del self.message_queue[client_id]
                        else:
                            client_socket.sendall(b"NO_MSG\n")

            except ConnectionResetError:
                with self.lock:
                    del self.clients[client_id]
                    if client_id in self.message_queue:
                        del self.message_queue[client_id]
                    print(f"Client '{client_id}' disconnected.\n")
                return


if __name__ == '__main__':
    print("===== Start Server =====")
    server_ip = input("IP-Address: ") or socket.gethostbyname(socket.gethostname())
    server_port = int(input("Port: ") or "2900")

    server = ChatServer(server_ip, server_port)
    server.start()