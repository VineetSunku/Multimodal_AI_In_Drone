import socket

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

client.connect(('10.250.2.130', 4681))

client.send("{'message': 'hello'}".encode())
print(client.recv(1024).decode())