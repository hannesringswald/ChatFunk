import socket
import sys
import platform
from threading import Thread

PORT = 4242


def get_my_ip():
    """Return the ipaddress of the local host

    On Debian-based systems we may get a rather strange address: 127.0.1.1
    See: https://www.debian.org/doc/manuals/debian-reference/ch05.en.html#_the_hostname_resolution

    """
    return socket.gethostbyname(socket.gethostname())


def threaded_client(connection, address):
    connection.send(str.encode("Please send username"))
    data = connection.recv(2048)
    username = data.decode()
    print(f"{username} at {address[0]}:{address[1]}")
    while True:
        print(f"Listening for {address[0]}:{address[1]} ...")
        data = connection.recv(2048)
        message = data.decode()
        if "stop" in message.lower():
            break
        reply = f"Echo to {username}: {message}"
        connection.send(str.encode(reply))
    print(f"Closing connection to {address[0]}:{address[1]}")
    connection.close()


if __name__ == "__main__":
    # Socket setup
    server_socket = socket.socket()
    try:
        server_socket.bind((get_my_ip(), PORT))
    except socket.error as e:
        print(e)
        server_socket.close()
        sys.exit(1)
    if platform.system() == "Windows":
        # Windows: No reaction to signals during socket.accept()
        #          => Wake up periodically from accept.
        server_socket.settimeout(1)
    # Start socket
    server_socket.listen()
    print(f"Listening on {get_my_ip()}:{PORT}")

    # Accept connections
    conn_cnt = 0
    try:
        while True:
            try:
                # print("Ready for a new connection ...\n")
                conn, addr = server_socket.accept()
                msg = f"New connection: {addr[0]}:{addr[1]}"
                print(msg)
                conn.send(msg.encode())
                Thread(target=threaded_client, args=(conn, addr), daemon=True).start()
                conn_cnt += 1  # TODO: De-register connections
                print(f"{conn_cnt} connections")
            except socket.timeout:  # Windows (Python >= 3.10: TimeoutError)
                continue
    except KeyboardInterrupt:
        print("\nStopping server due to user request")
    finally:
        print("Closing server socket")
        server_socket.close()
