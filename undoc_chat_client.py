import socket
import sys
import threading
from queue import Queue

MAX_MSG_LENGTH = 126


class ChatClient:
    def __init__(self, server_ip):
        self.server_ip = server_ip
        self.server_port = 2900
        self.client_socket = None
        self.client_id = None
        self.response_queue = Queue()
        self.stop_event = threading.Event()
        self.response_thread = threading.Thread(target=self.handle_server_message, daemon=True)

    def register(self, client_id):
        try:
            if not self.client_socket:
                self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client_socket.connect((self.server_ip, self.server_port))

            if not client_id:
                print("ERROR: Client ID must have at least one character")
                return False

            self.client_socket.sendall(client_id.encode())
            response = self.client_socket.recv(1024).decode()

            if response == "SUCCESS":
                self.client_id = client_id
                print(f"Client {client_id} registered")
                return True
            else:
                print(f"{response}")
                return False
        except (TimeoutError, ConnectionError):
            print("ERROR: Connection to server failed. Make sure the server is running and try again.")
            sys.exit(1)

    def handle_server_message(self):
        while not self.stop_event.is_set():
            try:
                # Set a timeout of 1 second
                self.client_socket.settimeout(1)
                message = self.client_socket.recv(1024).decode()
                # Reset the timeout
                self.client_socket.settimeout(None)

                if message == "SHUTDOWN":
                    print(
                        "\n!!! You have been disconnected from the server because it has been shut down. Press any key to exit.!!!")
                    self.stop_event.set()
                    self.disconnect()
                    break
                else:
                    self.response_queue.put(message)
            except socket.timeout:
                # If a timeout occurs, just continue the loop
                continue
            except ConnectionResetError:
                print("\n!!! Unexpectedly lost connection to server. Press any key to exit.!!!")
                self.stop_event.set()
                break

    def list_other_clients(self):
        request = "LIST"
        self.client_socket.send(request.encode())
        response = self.response_queue.get()
        print(f"Other clients logged in:\n{response}")

    def send_message(self, recipient, message):
        request = f"SEND {recipient} {message}"
        self.client_socket.send(request.encode())

    def check_messages(self):
        request = "CHECK"
        self.client_socket.send(request.encode())
        response = self.response_queue.get()
        if response == "EMPTY":
            print("No messages")
        else:
            print(response)

    def disconnect(self):
        self.stop_event.set()
        request = "DISCONNECT"
        self.client_socket.send(request.encode())

    def quit(self):
        print("Old messages:")
        self.check_messages()
        print(f"Closing down Session.\nGoodbye {self.client_id}!")
        self.disconnect()

    def run(self):
        while True:
            cid = input("Choose client ID: ").strip()
            if self.register(cid):
                break

        # Start a separate thread to listen for server messages
        self.response_thread.start()
        while not self.stop_event.is_set():
            print("====== Minimal Chat System ======")
            print("1: other Clients logged in")
            print("2: Send message")
            print("3: Check incoming messages")
            print("4: Quit")
            selection = input("Your selection: ")

            if self.stop_event.is_set():
                break
            else:
                if selection == "1":
                    chat_client.list_other_clients()
                elif selection == "2":
                    recip = input("Send message to: ")
                    if recip == chat_client.client_id:
                        print("ERROR: You cannot send a message to yourself.")
                    else:
                        msg = input("Your message: ")
                        if len(msg) > MAX_MSG_LENGTH:
                            print("ERROR: Message too long, please limit to 126 characters")
                        else:
                            chat_client.send_message(recip, msg)
                elif selection == "3":
                    chat_client.check_messages()
                elif selection == "4":
                    chat_client.quit()
                else:
                    print("Invalid selection. Please try again.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python undoc_chat_client.py <server_ip>")
        sys.exit(1)

    serv_ip = sys.argv[1]
    chat_client = ChatClient(serv_ip)
    chat_client.run()
