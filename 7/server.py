import socket
from collections import deque
from select import select
from concurrent.futures import ThreadPoolExecutor as Pool
from fib import fib

pool = Pool(10)

tasks = deque()
recv_wait = dict() # Mapping socket -> tasks (generators)
send_wait = dict()
future_wait = dict()

future_notify, future_event = socket.socketpair()

def future_done(future):
    tasks.append(future_wait.pop(future))
    future_notify.send(b'done')

def future_monitor():
    while True:
        yield 'recv', future_event
        future_event.recv(100)


class AsyncSocket(object):
    def __init__(self, sock):
        self.sock = sock

    def recv(self, size):
        yield 'recv', self.sock
        return self.sock.recv(size)

    def send(self, data):
        yield 'send', self.sock
        return self.sock.send(data)

    def accept(self):
        yield 'recv', self.sock
        client, addr = self.sock.accept()
        return AsyncSocket(client), addr

    def __getattr__(self, name):
        return getattr(self.sock, name)


def run():
    while any([tasks, recv_wait, send_wait]):
        while not tasks:
            # No active task to run, wait for I/O
            can_recv, can_send, _ = select(recv_wait, send_wait, [])
            for s in can_recv:
                tasks.append(recv_wait.pop(s))
            for s in can_send:
                tasks.append(send_wait.pop(s))
        task = tasks.popleft()
        try:
            why, what = next(task)

            if why == 'recv':
                recv_wait[what] = task
            elif why == 'send':
                send_wait[what] = task
            elif why == 'future':
                future_wait[what] = task

                what.add_done_callback(future_done)

            else:
                raise RuntimeError("ARG!")

        except StopIteration:
            print("task done")

def fib_server(address):
    sock = AsyncSocket(socket.socket(socket.AF_INET, socket.SOCK_STREAM))
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    sock.bind(address)
    sock.listen(5)
    while True:
        client, addr = yield from sock.accept()
        print("Connected from", addr)

        tasks.append(fib_handler(client))

def fib_handler(client):
    while True:
        req = yield from client.recv(100)
        if not req:
            break
        try:
            n = int(req)
        except:
            if req == b'\x04':
                break
            print('"{}" is not an integer'.format(req))
            continue

        future = pool.submit(fib, n)
        yield 'future', future
        result = future.result() #BLOCKSS

        resp = str(result).encode() + b'\n'

        yield from client.send(resp)
    print("Connection closed.")
    client.close()

if __name__ == '__main__':
    tasks.append(fib_server(('', 1234)))
    tasks.append(future_monitor())
    run()
