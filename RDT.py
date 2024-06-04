import random
import socket
import time

from Header import RDTHeader
from socket import *
import threading


class RDTSocket():
    def __init__(self) -> None:
        """
        You shold define necessary attributes in this function to initialize the RDTSocket
        """
        #############################################################################
        self.proxy_server_addr = None
        self.address = None
        self.socket = socket(AF_INET, SOCK_DGRAM)
        # self.connected = False
        # self.listening_accept = True

        #服务器socket使用:
        self.count = 0
        self.peer_info = {}

        #客户端socket、服务器连接socket使用:
        self.seq_num = 0
        self.ack_num = 0

        #客户端socket使用:
        self.target_address = None
        self.client_receiving = None
        self.client_sending = None
        self.lock = threading.Lock()
        self.sender_buffer = {}
        # self.sender_window = None
        self.sending_finish = False
        self.rwnd = 4

        #服务器连接socket使用:
        self.receiver_buffer = {}
        self.receiver_window = None
        self.finished_seq_num = None
        self.data_buffer = ''
        self.finished_data = []

        #############################################################################
        pass

    def bind(self, address: (str, int)):  # type: ignore
        """
        When trying to establish a connection. The socket must be bound to an address 
        and listening for connections. address is the address bound to the socket on 
        the other end of the connection.

     
        
        params: 
            address:    Target IP address and its port
        """
        #############################################################################
        # if self.connected:
        #     raise Exception("Socket already connected, could not bind again.")
        try:
            self.socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            self.socket.bind(address)
            self.address = address
            print("Socket bound successfully:", address)
        except OSError as e:
            print("Error binding socket:", str(e))
        #############################################################################

    def accept(self):  # type: ignore
        """
        When using this SOCKET to create an RDT SERVER, it should accept the connection
        from a CLIENT. After that, an RDT connection should be established.
        Please note that this function needs to support multithreading and be able to 
        establish multiple socket connections. Messages from different sockets should 
        be isolated from each other, requiring you to multiplex the data received at 
        the underlying UDP.

        This function should be blocking.
        在使用此SOCKET创建RDT服务器时，它应该接受来自客户端的连接。之后，应该建立一个RDT连接。请注意，
        此函数需要支持多线程，并能够建立多个套接字连接。来自不同套接字的消息应该相互隔离，
        这要求你在底层UDP上多路复用接收到的数据。

        此函数应该是阻塞的。

        """

        #############################################################################
        # while not self.listening_accept:
        #     time.sleep(1)
        while True:
            try:
                # 接收来自客户端的连接请求
                data, _ = self.socket.recvfrom(1024)
                header = RDTHeader().from_bytes(data)
                client_address = self.list_to_tuple(header.Source_address)
                print("服务器接收数据，来自:", header.Source_address)
                if header.SYN == 1:
                    print("接收的是第一次握手")

                    if client_address not in self.peer_info:
                        seq_num = random.randint(0, 2 ** 32 - 1)
                        ack_num = header.SEQ_num + 1
                        # self.peer_info[client_address] = (seq_num, ack_num, 12021 + self.count)
                        self.peer_info[client_address] = (seq_num, ack_num, self.address[1])
                        self.count = self.count + 1
                        print("receive.peer_info:", self.peer_info)
                    else:
                        seq_num = self.peer_info[client_address][0]
                        ack_num = self.peer_info[client_address][1]
                    syn_ack_header = RDTHeader(SYN=1, ACK=1, SEQ_num=seq_num, ACK_num=ack_num)
                    syn_ack_header.Source_address = self.tuple_to_list((self.address[0], self.peer_info[client_address][2]))
                    syn_ack_header.Target_address = self.tuple_to_list(client_address)
                    syn_ack_header.test_case = 20
                    print("服务器尝试发送第二次握手")
                    self.print_header(syn_ack_header)
                    self.socket.sendto(syn_ack_header.to_bytes(), self.proxy_server_addr)
                elif (header.ACK == 1 and client_address in self.peer_info
                      and header.ACK_num - 1 == self.peer_info[client_address][0]):
                    print("接收的是第三次握手")
                    # client_thread = threading.Thread(target=handle_client, args=(client_address))
                    # client_thread.start()
                    # if self.conn_socket is None:
                    conn_socket = RDTSocket()
                    conn_socket.bind((self.address[0], self.peer_info[client_address][2]))
                    conn_socket.address = (self.address[0], self.peer_info[client_address][2])
                    conn_socket.proxy_server_addr = self.proxy_server_addr
                    conn_socket.seq_num = self.peer_info[client_address][0]
                    conn_socket.ack_num = self.peer_info[client_address][1]
                    print("创建conn_socket:", conn_socket.address)
                    # client_thread = threading.Thread(target=self.handle_client, args=client_address)
                    # client_thread.start()
                    self.socket.close()
                    break
            except Exception as e:
                raise e
        return conn_socket
        #############################################################################


    def connect(self, address: (str, int)):  # type: ignore
        """
        When using this SOCKET to create an RDT client, it should send the connection
        request to target SERVER. After that, an RDT connection should be established.
        
        params:
            address:    Target IP address and its port
        """
        #############################################################################
        try:
            # 实现三次握手
            #syn_packet = RDTHeader(syn=1)
            #self.socket.sendto(syn_packet.to_bytes(), address)

            # 第一次握手：客户端发送SYN请求
            self.seq_num = random.randint(0, 2 ** 32 - 1)
            syn_header = RDTHeader(SYN=1, SEQ_num=self.seq_num)
            syn_header.Source_address = self.tuple_to_list(self.address)
            syn_header.Target_address = self.tuple_to_list(address)
            syn_header.test_case = 20
            print("客户端尝试发送第一次握手")
            self.print_header(syn_header)
            self.socket.sendto(syn_header.to_bytes(), self.proxy_server_addr)
            time.sleep(3)
            print("客户端接收第二次握手")
            data, _ = self.socket.recvfrom(1024)
            syn_ack_header = RDTHeader().from_bytes(data)
            #server_addr = self.create_address(syn_ack_packet.Source_address)
            # print("作为客户端，接收第二次握手")
            if syn_ack_header.SYN == 1 and syn_ack_header.ACK == 1 and syn_ack_header.ACK_num == self.seq_num + 1:
                self.ack_num = syn_ack_header.SEQ_num + 1
                #server_addr = address
                self.target_address = self.list_to_tuple(syn_ack_header.Source_address)
                # addr = self.socket.getsockname()
                # connection_key = (addr[0], addr[1], address[0], address[1])
                # self.connections[connection_key] = self # 存下socket
                # print("self.connections大小为")
                # print(len(self.connections))
                # 第三次握手：发送ACK确认
                ack_header = RDTHeader(ACK=1, ACK_num=syn_ack_header.SEQ_num + 1)
                ack_header.Source_address = self.tuple_to_list(self.address)
                ack_header.Target_address = self.tuple_to_list(address)
                ack_header.test_case = 20
                print("客户端尝试发送第三次握手")
                self.print_header(ack_header)
                self.socket.sendto(ack_header.to_bytes(), self.proxy_server_addr)

                # self.connected = True
                print("作为客户端，建立连接成功")
            else:
                # 握手失败
                print("收到无效的握手响应。握手失败。")
        except Exception as e:
            raise e
        #############################################################################
        # raise NotImplementedError()

    def send(self, data=None, tcpheader=None, test_case=0):
        """
        RDT can use this function to send specified data to a target that has already 
        established a reliable connection. Please note that the corresponding CHECKSUM 
        for the specified data should be calculated before computation. Additionally, 
        this function should implement flow control during the sending phase. Moreover, 
        when the data to be sent is too large, this function should be able to divide 
        the data into multiple chunks and send them to the destination in a pipelined 
        manner.
        
        params:
            data:       The data that will be sent.
            tcpheader:  Message header.Include SYN, ACK, FIN, CHECKSUM, etc. Use this
                        attribute when needed.
            test_case:  Indicate the test case will be used in this experiment
        """
        #############################################################################
        time.sleep(5)
        print(data)
        data = data.encode()

        # self.receiving = True
        self.client_receiving = threading.Thread(target=self.client_receiver)
        self.client_sending = threading.Thread(target=self.client_sender, args=(data, test_case))
        self.client_receiving.start()
        self.client_sending.start()
        self.client_sending.join()
        # print("self.client_sending.join()")
        self.client_receiving.join()
        # print("self.client_receiving.join()")

    def recv(self):
        """
        You should implement the basic logic for receiving data in this function, and 
        verify the data. When corrupted or missing data packets are detected, a request 
        for retransmission should be sent to the other party.
        
        This function should be bolcking.
        """
        #############################################################################
        while True:
            print("waiting for data...")
            data, _ = self.socket.recvfrom(1024)
            packet = RDTHeader().from_bytes(data)
            client_address = self.list_to_tuple(packet.Source_address)
            checksum_local = self.cal_checksum(packet.to_bytes())
            test_case = packet.test_case
            print(packet.CHECKSUM)
            print(checksum_local)
            if checksum_local == packet.CHECKSUM:
                print(packet.SEQ_num + 1)
                print(self.ack_num)
                # if packet.SEQ_num + 1 < self.ack_num:#该包其实已经正确收到
                #     continue
                if packet.SEQ_num + 1 <= self.ack_num:#判断紧接或已经正确收到
                    with self.lock:
                        self.ack_num = (packet.SEQ_num + 1) % (2 ** 32)
                        ack_header = RDTHeader(ACK=1, SEQ_num=self.seq_num, ACK_num=self.ack_num, RWND=4-len(self.receiver_buffer))
                        ack_header.Source_address = self.tuple_to_list(self.address)
                        ack_header.Target_address = self.tuple_to_list(client_address)
                        ack_header.test_case = test_case
                        self.print_header(ack_header)
                        self.socket.sendto(ack_header.to_bytes(), self.proxy_server_addr)
                        print("已发送ACK响应:", self.ack_num)
                        self.ack_num = self.ack_num + len(packet.PAYLOAD)
                    self.data_buffer = self.data_buffer + packet.PAYLOAD
                    if len(self.data_buffer) == packet.LEN:
                        print("已收到一条完整数据")
                        self.finished_data.append(self.data_buffer)
                        self.data_buffer = ''
                        # break
                    for key, value in self.receiver_buffer:
                        if value[0].SEQ_num + 1 == self.ack_num:
                            with self.lock:
                                self.ack_num = (value[0].SEQ_num + 1) % (2 ** 32)
                                ack_header = RDTHeader(ACK=1, SEQ_num=self.seq_num, ACK_num=self.ack_num, RWND=4-len(self.receiver_buffer))
                                ack_header.Source_address = self.tuple_to_list(self.address)
                                ack_header.Target_address = self.target_address(client_address)
                                ack_header.test_case = value[0].test_case
                                self.print_header(ack_header)
                                self.socket.sendto(ack_header.to_bytes(), self.proxy_server_addr)
                                print("已发送ACK响应:", self.ack_num)
                                self.ack_num = self.ack_num + len(packet.PAYLOAD)
                                del self.receiver_buffer[key]
                            self.data_buffer = self.data_buffer +value[0].PAYLOAD
                            if len(self.data_buffer) == packet.LEN:
                                print("已收到一条完整数据")
                                self.finished_data.append(self.data_buffer)
                                self.data_buffer = ''
                                # break
                    #直接输出data并发送ACK包，检查缓冲区是否存在紧接
                else:
                    print(len(self.receiver_buffer))
                    if len(self.receiver_buffer) < 5:#判断缓冲区是否未满
                        with self.lock:
                            self.receiver_buffer[packet.SEQ_num] = (packet)
                        #未满，存入缓冲区
                    else:
                        continue
                        #已满，丢弃，不发送NAK包
            else:
                # 错误数据，发送NAK包并丢弃
                with self.lock:
                    nak_header = RDTHeader(ACK=0, SEQ_num=self.seq_num, ACK_num=self.ack_num)
                    nak_header.Source_address = self.tuple_to_list(self.address)
                    nak_header.Target_address = self.tuple_to_list(client_address)
                    nak_header.test_case = test_case
                    self.print_header(nak_header)
                    self.socket.sendto(nak_header.to_bytes(), self.proxy_server_addr)
                    print("已请求重传")
        self.socket.close()


        # self.socket.sendto(client_address)
        # print(data)
        # return data
        #############################################################################
        # raise NotImplementedError()

    def close(self):
        """
        Close current RDT connection.
        You should follow the 4-way-handshake, and then the RDT connection will be terminated.
        """
        #############################################################################
        self.socket = socket(AF_INET, SOCK_DGRAM)
        self.socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        # print(self.address)
        self.socket.bind(self.address)                                      #
        #############################################################################
        # raise NotImplementedError()

    def print_header(self, header: RDTHeader):
        print(header.test_case)
        print(header.Source_address)
        print(header.Target_address)
        print(header.SYN)
        print(header.FIN)
        print(header.ACK)
        print(header.SEQ_num)
        print(header.ACK_num)
        print(header.LEN)
        print(header.CHECKSUM)
        print(header.RWND)
        print(header.Reserved)
        print(header.PAYLOAD)
        # print(header.to_bytes())

    def tuple_to_list(self, ip_port_tuple):
        ip, port = ip_port_tuple
        ip_parts = list(map(int, ip.split('.')))
        return ip_parts + [port]

    def list_to_tuple(self, ip_port_list):
        ip_parts = ip_port_list[:4]
        port = ip_port_list[4]
        ip = '.'.join(map(str, ip_parts))
        return (ip, port)

    def cal_checksum(self, data):
        #计算数据包的校验和
        # 1.将校验和字段先设置为0
        checksum = 0
        data = data[0:32]+b"\x00"+data[34:]
        data = data[1:]
        # 2.将数据划分为16位(2字节)的段
        segments = []
        for i in range(0, len(data), 2):
            segment = data[i:i + 2]
            segments.append(segment)
        # 如果数据长度为奇数，最后一个字节用0填充
        if len(data) % 2 != 0:
            segments.append(b'\x00')

        # 3.计算所有段的总和
        for segment in segments:
            checksum += int.from_bytes(segment, byteorder='big')

        # 4.将32位校验和的高16位和低16位相加
        while checksum > 0xffff:
            checksum = (checksum >> 16) + (checksum & 0xffff)

        # 5.取补码作为最终校验和
        checksum = ~checksum & 0xffff

        return checksum

    def client_receiver(self):
        print("客户端receiver启动")
        while not self.sending_finish and self.sender_buffer:
            data, _ = self.socket.recvfrom(1024)
            # packet = RDTHeader().from_bytes(data)
            ack_packet = RDTHeader().from_bytes(data)
            finished_seq_num = ack_packet.ACK_num - 1
            self.rwnd = ack_packet.RWND
            if ack_packet.ACK == 1:
                # 从缓冲区删除
                print(self.sender_buffer)
                print("从缓冲区删除:", finished_seq_num)
                with self.lock:
                    keys_to_delete = [key for key, value in self.sender_buffer.items() if key <= finished_seq_num]
                    for key in keys_to_delete:
                        del self.sender_buffer[key]
                # print(self.sender_buffer)
            else:
                # 等待重传
                print("等待重传")
            time.sleep(1)

        # del self.sender_buffer[key]

    def client_sender(self, data, test_case):
        data_len = len(data) # 文件总长度
        while data or self.sender_buffer:
            if len(self.sender_buffer) < 5 and data and self.rwnd > 0:
                chunk = data[:256]  # 最大256字节的数据块
                data = data[256:]
                packet = RDTHeader(SEQ_num=self.seq_num, ACK_num=self.ack_num, LEN=data_len, CHECKSUM=0, PAYLOAD=chunk.decode())
                packet.Source_address = self.tuple_to_list(self.address)
                packet.Target_address = self.tuple_to_list(self.target_address)
                packet.CHECKSUM = self.cal_checksum(packet.to_bytes())
                packet.test_case = test_case
                with self.lock:
                    self.sender_buffer[self.seq_num] = (packet, time.time())
                    self.print_header(packet)
                    self.socket.sendto(packet.to_bytes(), self.target_address)
                    print("已发送一块数据:", self.seq_num)
                    self.seq_num = (self.seq_num + len(chunk) )% (2 ** 32)
                # print(type(self.send_buffer))
            else:
                print("查看超时重发")
                print(self.sender_buffer)
                for key, value in self.sender_buffer.items():
                    if time.time() - value[1] > 5:
                        with self.lock:
                            new_value = (value[0], time.time())
                            self.sender_buffer[key] = new_value
                            self.print_header(value[0])
                            self.socket.sendto(value[0].to_bytes(), self.target_address)
                            print("超时重发一块数据:", key)
            time.sleep(1)
        self.sending_finish = True
        # print("set self.sending_finish = True")

    def server_getdata(self):

        # print("获取数据")
        if len(self.finished_data) > 0:
            data = self.finished_data.pop()
        else:
            data = ""
        return data

