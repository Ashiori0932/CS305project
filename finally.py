import socket

proxy_server_address = ('10.16.52.94', 12234)   # ProxyServerAddress
fromSenderAddr = ('10.16.52.94', 12345)         # FromSender
toReceiverAddr = ('10.16.52.94', 12346)         # ToSender
fromReceiverAddr = ('10.16.52.94', 12347)       # FromReceiver
toSenderAddr = ('10.16.52.94', 12348)           # ToReceiver

resultAddr = ('10.16.52.94', 12230)

#TODO change the adress to your address
sender_address = ("10.26.97.249", 12344)         # Your sender address
receiver_address = ("10.26.97.249", 12349)       # Your receiver address

client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_sock.connect(resultAddr)

client_sock.sendall(f"{sender_address}-{receiver_address}:{8}".encode())

response = client_sock.recv(1024)
print(response)
client_sock.close()