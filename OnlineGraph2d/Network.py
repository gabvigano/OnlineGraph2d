import pickle
import socket
from _thread import start_new_thread


def get_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except:  # noqa
        return None


class Server:
    def __init__(self, server_ip, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_number = 0
        self.sock.bind((server_ip, port))
        self.to_send, self.to_get = {}, {}
        start_new_thread(self.wait_connection, ())

    def wait_connection(self):
        connection_number = 0
        self.sock.listen()
        print('\nSERVER: waiting for connection')

        while True:
            connection_number += 1

            connection, address = self.sock.accept()

            print(f'SERVER: connected to: {address[0]}')

            start_new_thread(self.threaded_client, (connection, connection_number))

    def threaded_client(self, connection, connection_number):  # noqa
        connection.sendall(pickle.dumps(connection_number))

        while True:
            try:
                data = pickle.loads(connection.recv(1024))

                if not data:
                    print('SERVER: disconnected')
                    del self.to_get[connection_number]
                    break
                else:
                    self.to_get[connection_number] = data

                connection.sendall(self.to_send)

            except Exception as e:
                print(f'SERVER: {e}')
                del self.to_get[connection_number]
                break

        print('SERVER: connection lost')
        connection.close()

    def send(self, data):
        self.to_send = pickle.dumps(data)
        return self.to_get


class Client:
    def __init__(self, server_ip, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            self.sock.connect((server_ip, port))
            self.client_number = pickle.loads(self.sock.recv(1024))
            print(f'\nCLIENT: connection successful (client number: {self.client_number})')
        except socket.error:
            print('\nCLIENT: connection failed')

    def send(self, data):
        self.sock.send(pickle.dumps(data))
        return pickle.loads(self.sock.recv(1024))
