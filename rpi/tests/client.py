import socket
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #Computer to RPi socket initialize
server.settimeout(30)
IS_DISCONNECTED = 1
try:
    print("Connecting to RaspberryPi")
    server.connect(('10.14.1.100', 4681))
    print("Connected to RaspberryPi. It says: " + server.recv(1024).decode())
    IS_DISCONNECTED = 0
except (socket.timeout, ConnectionRefusedError, OSError) as e:
    print(f"Couldn't connect to RaspberryPi: {e}")
    
while not IS_DISCONNECTED:
        d=eval(server.recv(1024).decode())
        if d:
            print(d, type(d))