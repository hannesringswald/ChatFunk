import socket
import sys

MAX_MSG_LENGTH = 126


class ChatClient:
    def __init__(self, server_ip):
        self.server_ip = server_ip
        self.client_socket = None
        self.client_id = None

    def register(self, client_id):
        if not self.client_socket:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.server_ip, 2900))

        if not client_id:
            print("Client ID must have at least one character")
            return False

        self.client_socket.sendall(client_id.encode())
        response = self.client_socket.recv(MAX_MSG_LENGTH).decode()

        if response == "SUCCESS":
            self.client_id = client_id
            print(f"Client {client_id} registered")
            return True
        else:
            print(f"{response}")
            return False

    def list_other_clients(self):
        request = "LIST"
        self.client_socket.send(request.encode())
        response = self.client_socket.recv(1024).decode()
        print(f"Other clients logged in:\n{response}")

    def send_message(self, recipient, message):
        request = f"SEND {recipient} {message}"
        self.client_socket.send(request.encode())

    def check_messages(self):
        request = "CHECK"
        self.client_socket.send(request.encode())
        response = self.client_socket.recv(1024).decode()
        if response == "NO_MSG":
            print("No messages\n")
        else:
            print(response)

    def close(self):
        print("Old messages:")
        self.check_messages()
        if self.client_socket:
            self.client_socket.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python chat_client.py <server_ip>")
        exit()

    server_ip = sys.argv[1]
    chat_client = ChatClient(server_ip)

    while True:
        client_id = input("Choose client ID: ").strip()
        if chat_client.register(client_id):
            break

    print(f"Client {client_id} registered")

    while True:
        print("====== Minimal Chat System ======")
        print("1: other Clients logged in")
        print("2: Send message")
        print("3: Check incoming messages")
        print("4: Quit")
        selection = input("Your selection: ")

        if selection == "1":
            chat_client.list_other_clients()

        elif selection == "2":
            recipient = input("Recipient name: ")
            message = input("Message: ")
            chat_client.send_message(recipient, message)

        elif selection == "3":
            chat_client.check_messages()
        elif selection == "4":
            chat_client.close()
            exit()
        else:
            print("Invalid selection. Please try again.")
