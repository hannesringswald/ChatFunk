"""Module implementing a chat client.

This module provides the implementation of a chat client that can connect to a
server and enable communication with other clients also connected to the same server.

Usage example:

    $ python chat_client.py <server_ip>

Authors:
    Alexander Riedlinger <alexander.riedlinger@student.dhbw-vs.de>
"""

import socket
import sys
import threading
from queue import Queue


class ChatClient:
    """
    A class representing a client for a chat application.

    Args:
    server_ip (str): The IP address of the server.

    Attributes:
    server_ip (str): The IP address of the server.
    server_port (int): The port number of the server.
    client_socket (socket.socket): The socket object representing the client's
                                   connection to the server.
    client_id (str): The ID of the client.
    response_queue (Queue): A queue to store responses from the server.
    stop_event (threading.Event): An event to signal the response handling
                                  thread to stop.
    response_thread (threading.Thread): A thread to handle server messages.
    """
    def __init__(self, server_ip):
        """
        Initializes a new instance of the ChatClient class.

        Args:
        server_ip (str): The IP address of the server.
        """
        self.server_ip = server_ip
        self.server_port = 2900
        self.client_socket = None
        self.client_id = None
        self.response_queue = Queue()
        self.stop_event = threading.Event()
        self.response_thread = threading.Thread(target=self.handle_server_message,
                                                daemon=True)

    def register(self, client_id):
        """
        Registers the client with the server using the provided client ID.

        Args:
        client_id (str): The ID to register the client with.

        Returns:
        bool: True if the registration is successful, False otherwise.
        """
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
            print("ERROR: Connection to server failed. Make sure the server is "
                  "running and try again.")
            sys.exit(1)

    def handle_server_message(self):
        """
        Continuously listens for messages from the server and puts them in a
        response queue.
        If a "SHUTDOWN" message is received, sets the stop event, disconnects
        from the server, and exits the loop.
        """
        while not self.stop_event.is_set():
            try:
                # Set a timeout of 1 second
                self.client_socket.settimeout(1)
                message = self.client_socket.recv(1024).decode()
                # Reset the timeout
                self.client_socket.settimeout(None)

                if message == "SHUTDOWN":
                    print(
                        "\n!!! You have been disconnected from the server because"
                        " it has been shut down. Press any key to exit.!!!")
                    self.stop_event.set()
                    self.disconnect()
                    break
                else:
                    self.response_queue.put(message)
            except socket.timeout:
                # If a timeout occurs, just continue the loop
                continue
            except ConnectionResetError:
                print(
                    "\n!!! Unexpectedly lost connection to server. "
                    "Press any key to exit.!!!")
                self.stop_event.set()
                break

    def list_other_clients(self):
        """Sends a "LIST" request to the server to list all other clients
        currently logged in.

        Prints a formatted list of the other clients' IDs.
        """
        request = "LIST"
        self.client_socket.send(request.encode())
        response = self.response_queue.get()
        print(f"Other clients logged in:\n{response}")

    def send_message(self, recipient, message):
        """Sends a message to the specified recipient utilizing "SEND" request.

        Args:
            recipient (str): The ID of the client to send the message to.
            message (str): The message to send.

        """
        request = f"SEND {recipient} {message}"
        self.client_socket.send(request.encode())

    def check_messages(self):
        """Sends a "CHECK" request to the server to check for new messages.

        Prints any new messages that have been received since the last check.
        """
        request = "CHECK"
        self.client_socket.send(request.encode())
        response = self.response_queue.get()
        if response == "EMPTY":
            print("No messages")
        else:
            print(response)

    def disconnect(self):
        """
        Disconnect from the server by sending a "DISCONNECT" request and setting
        the stop_event flag.
        """
        self.stop_event.set()
        request = "DISCONNECT"
        self.client_socket.send(request.encode())

    def quit(self):
        """
        Disconnect from the server and print any old messages before exiting
        the client.
        """
        print("Old messages:")
        self.check_messages()
        print(f"Closing down Session.\nGoodbye {self.client_id}!")
        self.disconnect()

    def run(self):
        """
        Starts the chat client and listens for user input to interact with the
        chat server.

        The method first prompts the user to select a client ID and attempts to
        register with the server using this ID.
        If the registration is successful, the method starts a separate thread
        to listen for incoming server messages.

        The method then enters a loop to process user input. The user can choose
        to list other logged-in clients, send a message to another client, check
        for incoming messages, or quit the chat system. Invalid selections will
        result in an error message.

        """
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
                    self.list_other_clients()
                elif selection == "2":
                    recip = input("Send message to: ")
                    if recip == self.client_id:
                        print("ERROR: You cannot send a message to yourself.")
                    else:
                        msg = input("Your message: ")
                        if len(msg) > 126:
                            print("ERROR: Message too long, please limit to 126 characters")
                        else:
                            self.send_message(recip, msg)
                elif selection == "3":
                    self.check_messages()
                elif selection == "4":
                    self.quit()
                else:
                    print("Invalid selection. Please try again.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python chat_client.py <server_ip>")
        sys.exit(1)

    serv_ip = sys.argv[1]
    chat_client = ChatClient(serv_ip)
    chat_client.run()