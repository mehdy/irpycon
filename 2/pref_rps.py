from threading import Thread
import socket
import time

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('localhost', 1234))
sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

n = 0
status = True

def monitor():
    global n, status
    while status:
        time.sleep(1)
        print(n, 'reqs/sec')
        n = 0

Thread(target=monitor).start()

while True:
    try:
        sock.send(b'1')
        resp = sock.recv(100)
        n += 1
    except:
        break

status = False
sock.close()
