import threading
import time

from RDT import RDTSocket

proxy_server_address = ('10.16.52.94', 12234)   # ProxyServerAddress
fromSenderAddr = ('10.16.52.94', 12345)         # FromSender
toReceiverAddr = ('10.16.52.94', 12346)         # ToSender
fromReceiverAddr = ('10.16.52.94', 12347)       # FromReceiver
toSenderAddr = ('10.16.52.94', 12348)           # ToReceiver

resultAddr = ('10.16.52.94', 12230)

#TODO change the adress to your address
sender_address = ("10.26.97.249", 12344)         # Your sender address
receiver_address = ("10.26.97.249", 12349)       # Your receiver address


# proxy_server_address = ('127.0.0.1', 12234)
# fromSenderAddr = ('127.0.0.1', 12345)
# toReceiverAddr = ('127.0.0.1', 12346)
# fromReceiverAddr = ('127.0.0.1', 12347)
# toSenderAddr = ('127.0.0.1', 12348)
#
# sender_address = ("127.0.0.1", 12244)
# receiver_address = ("127.0.0.1", 12249)
# resultAddr = ("127.0.0.1", 12230)


receiver_sock = RDTSocket()
sock = receiver_sock
sock.proxy_server_addr = fromReceiverAddr
sock.bind(receiver_address)
server_sock = sock.accept()
server_receiving = threading.Thread(target=server_sock.recv)
server_receiving.start()
while True:
    time.sleep(1)
    data = server_sock.server_getdata()
    if data != "":
        print("write to file", len(data))
        with open('transmit.txt', 'wb') as f:
            # while True:
            #     # data, _ = server_sock.recv()
            #     # #############################################################################
            #     # # TODO: Save all data to the file, and stop this loop when the client
            #     # #       close the connection.
            #     # if not data:  # Assuming the client closes the connection when no more data is sent.
            #     #     break
            #     # print("write data:")
            #     # print(data)
            f.write(data.encode())
                # break
            #############################################################################

