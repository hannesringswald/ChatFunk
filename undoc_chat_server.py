import socket
import sys
from threading import Thread, Lock
from collections import defaultdict
from queue import Queue
import time


class ChatServer:
    def __init__(self, ip_addr=socket.gethostbyname(socket.gethostname()), port=2900):
        self.ip_addr = ip_addr
        self.port = port
        self.clients = {}
        self.lock = Lock()
        self.message_queue = defaultdict(Queue)
        self.running = False

    def __enter__(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.server_socket.bind((self.ip_addr, self.port))
        except socket.error as e:
            print(e)
            self.server_socket.close()
            sys.exit(1)
        self.server_socket.listen()
        self.server_socket.settimeout(1)
        self.running = True
        print(f"Listening on {self.ip_addr}:{self.port}")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.running = False
        for client_socket in self.clients.values():
            try:
                client_socket.sendall(b"SHUTDOWN")
            except Exception as e:
                print(f"Error sending SHUTDOWN to client '{client_id}': {e}")
        self.server_socket.close()

    def start(self):
        threads = []
        try:
            while self.running:
                try:
                    client_socket, address = self.server_socket.accept()
                    client_thread = Thread(target=self.handle_client,
                                           args=(client_socket, address))
                    client_thread.start()
                    threads.append(client_thread)
                except socket.timeout:
                    pass
        except KeyboardInterrupt:
            print("\nStopping server due to user request")
        finally:
            self.stop()
            for thread in threads:
                thread.join()

    def stop(self):
        self.running = False
        countdown = 5

        with self.lock:
            for client_id, client_socket in self.clients.items():
                try:
                    client_socket.sendall(b"SHUTDOWN")
                except Exception as e:
                    print(f"Error sending SHUTDOWN to client '{client_id}': {e}")

            while countdown > 0:
                print(f"Server shutting down in {countdown} seconds...")
                time.sleep(1)
                countdown -= 1

            # Make sure everything is closed properly
            for client_socket in self.clients.values():
                with client_socket:
                    pass
            with self.server_socket:
                pass

    def handle_client(self, client_socket, address):
        with client_socket:
            while True:
                client_id = client_socket.recv(1024).decode()
                if not client_id:
                    continue

                with self.lock:
                    if client_id in self.clients:
                        client_socket.send(b"ERROR: Client ID already taken. "
                                           b"Please choose another one.")
                    else:
                        self.clients[client_id] = client_socket
                        print(f"Client '{client_id}' connected from {address}\n")
                        client_socket.send(b"SUCCESS")
                        break

            while True:
                try:
                    message = client_socket.recv(1024).decode()
                    if not message:
                        continue

                    parts = message.split(" ")
                    command = parts[0]

                    if command == "SEND":
                        recipient = parts[1]
                        msg = " ".join(parts[2:])
                        if recipient not in self.clients:
                            # Message lost for unknown recipient
                            pass
                        else:
                            with self.lock:
                                self.message_queue[recipient].put((client_id, msg))

                    elif command == "LIST":
                        with self.lock:
                            other_clients = [cid for cid in self.clients if cid
                                             != client_id]
                            if len(other_clients) != 0:
                                client_socket.sendall("\n".join(other_clients)
                                                      .encode())
                            else:
                                client_socket.sendall(b"Only you at the moment!")

                    elif command == "CHECK":
                        with self.lock:
                            if client_id in self.message_queue:
                                queue = self.message_queue[client_id]
                                messages = []
                                while not queue.empty():
                                    sender, msg = queue.get()
                                    messages.append(f"{sender}: {msg}")
                                client_socket.sendall("\n".join(messages).encode())
                                del self.message_queue[client_id]
                            else:
                                client_socket.sendall(b"EMPTY")

                    elif command == "DISCONNECT":
                        with self.lock:
                            del self.clients[client_id]
                            if client_id in self.message_queue:
                                del self.message_queue[client_id]
                                with client_socket:
                                    pass
                            print(f"Client '{client_id}' disconnected.\n")
                        return

                except ConnectionResetError:
                    with self.lock:
                        del self.clients[client_id]
                        if client_id in self.message_queue:
                            del self.message_queue[client_id]
                        print(f"Client '{client_id}' disconnected.\n")
                    return


if __name__ == '__main__':
    print("===== Start Server =====")
    default_ip = socket.gethostbyname(socket.gethostname())
    server_ip = input(f"IP-Address (local, default={default_ip}): ") or default_ip
    server_port = int(input("Port (default=2900): ") or "2900")

    with ChatServer(server_ip, server_port) as server:
        server.start()
