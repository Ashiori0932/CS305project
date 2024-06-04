import time

from RDT import RDTSocket

# proxy_server_address = ('10.16.52.94', 12234)   # ProxyServerAddress
# fromSenderAddr = ('10.16.52.94', 12345)         # FromSender
# toReceiverAddr = ('10.16.52.94', 12346)         # ToSender
# fromReceiverAddr = ('10.16.52.94', 12347)       # FromReceiver
# toSenderAddr = ('10.16.52.94', 12348)           # ToReceiver
#
# resultAddr = ('10.16.52.94', 12230)
#
# #TODO change the adress to your address
# sender_address = ("10.26.97.249", 12344)         # Your sender address
# receiver_address = ("10.26.97.249", 12349)       # Your receiver address


proxy_server_address = ('127.0.0.1', 12234)
fromSenderAddr = ('127.0.0.1', 12345)
toReceiverAddr = ('127.0.0.1', 12346)
fromReceiverAddr = ('127.0.0.1', 12347)
toSenderAddr = ('127.0.0.1', 12348)

sender_address = ("127.0.0.1", 12240)
receiver_address = ("127.0.0.1", 12249)
resultAddr = ("127.0.0.1", 12230)

sender_sock = RDTSocket()

sock = sender_sock
sock.proxy_server_addr = fromSenderAddr

sock.bind(sender_address)
sock.connect(receiver_address)
test_case = 8
print("test_case:", test_case)
time.sleep(1)
file_path = 'original.txt'
data_blocks = []
with open(file_path, 'rb') as file:
    while True:
        block = file.read(1024)
        print("reading...")
        if not block:
            break
        data_blocks.append(block.decode())
        # all_data = b''.join(data_blocks)
all_data = ''.join(data_blocks)
# return all_data
sock.send(data=all_data, test_case=test_case)
# data = "Short Message test again"
# sock.send(data=data, test_case=0)