import socket
import sys

MAX_MSG_LENGTH = 126


class ChatClient:
    def __init__(self, server_ip):
        self.server_ip = server_ip
        self.server_port = 2900
        self.client_socket = None
        self.client_id = None

    def register(self, client_id):
        if not self.client_socket:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.server_ip, self.server_port))

        if not client_id:
            print("Client ID must have at least one character")
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

    def disconnect(self):
        request = "DISCONNECT"
        self.client_socket.send(request.encode())
        self.client_socket.close()
        print(f"Closing down Session.\nGoodbye {self.client_id}!")

    def close(self):
        print("Old messages:")
        self.check_messages()
        if self.client_socket:
            self.disconnect()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python chat_client.py <server_ip>")
        sys.exit(1)

    serv_ip = sys.argv[1]
    chat_client = ChatClient(serv_ip)

    while True:
        cid = input("Choose client ID: ").strip()
        if chat_client.register(cid):
            break

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
            recip = input("Send message to: ")
            if recip == chat_client.client_id:
                print("You cannot send a message to yourself.")
            else:
                msg = input("Your message: ")
                if len(msg) > MAX_MSG_LENGTH:
                    print("Message too long, please limit to 126 characters")
                else:
                    chat_client.send_message(recip, msg)
        elif selection == "3":
            chat_client.check_messages()
        elif selection == "4":
            chat_client.close()
            sys.exit(0)
        else:
            print("Invalid selection. Please try again.")
