import socket
from threading import Thread
from fib import fib

def fib_server(address):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    sock.bind(address)
    sock.listen(5)
    while True:
        client, addr = sock.accept()
        print("Connected from", addr)
        thread = Thread(target=fib_handler, args=(client,)).start()

def fib_handler(client):
    while True:
        req = client.recv(100)
        if not req:
            break
        try:
            n = int(req)
        except:
            if req == b'\x04':
                break
            print('"{}" is not an integer'.format(req))
            continue
        result = fib(n)
        resp = str(result).encode() + b'\n'
        client.send(resp)
    print("Connection closed.")
    client.close()

if __name__ == '__main__':
    fib_server(('', 1234))
