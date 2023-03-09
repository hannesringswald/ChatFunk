import socket
import sys

client_socket = socket.socket()
LOCALHOST = '127.0.0.1'
PORT = 4242


try:
    host = sys.argv[1]  # server IP given on command line
except IndexError:
    host = LOCALHOST
    print(f"No server given on command line. Trying {host}")
try:
    print(f"Waiting for connection to {host}")
    client_socket.connect((host, PORT))
except socket.error as e:
    print(str(e))
    if host == LOCALHOST:
        print("Running locally on Debian based system? "
              "Then you may try 127.0.1.1 for connecting to server")
    sys.exit(1)

# Ack for connection
response = client_socket.recv(2048)
print(f"{response.decode()}")
# Send username
response = client_socket.recv(2048)
print(f"{response.decode()}")
username = input("Username: ")
client_socket.send(str.encode(username))
# Do the talk
while True:
    msg = input("Say something: ")
    if not msg:  # empty message not permitted in TCP
        continue
    client_socket.send(str.encode(msg))
    if "stop" in msg.lower():  # protocol: "stop" to close connection.
        break
    print("Listening ...")
    # Echo from Server
    response = client_socket.recv(2048)
    return_msg = response.decode()
    print(return_msg)

print("Closing connection")
client_socket.close()
