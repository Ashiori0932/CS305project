import random
import socket
import time
from collections import OrderedDict
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
        self.connections = {}

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
                # 如果是SYN请求, 三次握手
                if header.SYN == 1:
                    print("作为服务器，接收的是第一次握手")
                    print(client_address)
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
                    print("服务器发送端口为")
                    print((self.address[0], self.peer_info[client_address][2]))
                    self.print_header(syn_ack_header)
                    self.socket.sendto(syn_ack_header.to_bytes(), self.proxy_server_addr)
                elif (header.ACK == 1 and client_address in self.peer_info
                      and header.ACK_num - 1 == self.peer_info[client_address][0]):
                    print("接收的是第三次握手")
                    # client_thread = threading.Thread(target=handle_client, args=(client_address))
                    # client_thread.start()
                    # if self.conn_socket is None:
                    conn_socket = RDTSocket()
                    #print("服务器要绑定的地址：", (self.address[0], self.peer_info[client_address][2]))
                    #conn_socket.bind((self.address[0], self.peer_info[client_address][2]))
                    #print("accept时服务器绑定到的地址", conn_socket.socket.getsockname())
                    conn_socket.address = (self.address[0], self.peer_info[client_address][2])
                    conn_socket.proxy_server_addr = self.proxy_server_addr
                    conn_socket.seq_num = self.peer_info[client_address][0]
                    conn_socket.ack_num = self.peer_info[client_address][1]


                    key = (client_address[0], client_address[1], self.address[0], self.peer_info[client_address][2])
                    self.connections[key] = conn_socket  # 存下socket
                    print("服务器socket的key为：", key)
                    print("服务器self.connections大小为", len(self.connections))
                    print("创建conn_socket:", conn_socket.address)
                    print("已存储新建立的socket")
                    print("作为服务器，建立连接成功")
                    # client_thread = threading.Thread(target=self.handle_client, args=client_address)
                    # client_thread.start()
                    #self.socket.close()
                    break
            except Exception as e:
                raise e
        return self
        #############################################################################
    
    # def accept(self):
    #     """
    #     当使用此SOCKET创建RDT服务器时，它应该接受来自客户端的连接。之后，应该建立一个RDT连接。
    #     请注意，此函数需要支持多线程，并能够建立多个套接字连接。来自不同套接字的消息应该相互隔离，
    #     这要求你在底层UDP上多路复用接收到的数据。

    #     此函数应该是阻塞的。
    #     """
    #     while True:
    #         try:
    #             # 接收来自客户端的连接请求
    #             data, client_address = self.socket.recvfrom(1024)
    #             header = RDTHeader().from_bytes(data)
    #             client_address = self.list_to_tuple(header.Source_address)
    #             print("服务器接收到数据，来自:", client_address)

    #             # 如果是SYN请求，进行三次握手
    #             if header.SYN == 1:
    #                 print("作为服务器，接收到第一次握手")
    #                 if client_address not in self.peer_info:
    #                     seq_num = random.randint(0, 2 ** 32 - 1)
    #                     ack_num = header.SEQ_num + 1
    #                     self.peer_info[client_address] = (seq_num, ack_num, self.address[1])
    #                     print("已记录客户端信息:", self.peer_info)
    #                 else:
    #                     seq_num = self.peer_info[client_address][0]
    #                     ack_num = self.peer_info[client_address][1]

    #                 # 发送第二次握手的SYN-ACK包
    #                 syn_ack_header = RDTHeader(SYN=1, ACK=1, SEQ_num=seq_num, ACK_num=ack_num)
    #                 syn_ack_header.Source_address = self.tuple_to_list((self.address[0], self.peer_info[client_address][2]))
    #                 syn_ack_header.Target_address = self.tuple_to_list(client_address)
    #                 self.print_header(syn_ack_header)
    #                 self.socket.sendto(syn_ack_header.to_bytes(), client_address)

    #             elif header.ACK == 1 and client_address in self.peer_info and header.ACK_num - 1 == self.peer_info[client_address][0]:
    #                 print("接收到第三次握手")

    #                 # 创建新的连接套接字
    #                 conn_socket = RDTSocket()
    #                 conn_socket.address = (self.address[0], self.peer_info[client_address][2])
    #                 conn_socket.proxy_server_addr = self.proxy_server_addr
    #                 conn_socket.seq_num = self.peer_info[client_address][0]
    #                 conn_socket.ack_num = self.peer_info[client_address][1]

    #                 # 存储连接
    #                 key = (client_address[0], client_address[1], self.address[0], self.peer_info[client_address][2])
    #                 self.connections[key] = conn_socket
    #                 print("已建立连接，服务器套接字的key为:", key)
    #                 print("当前连接数:", len(self.connections))

    #                 # 返回连接的套接字实例
    #                 return conn_socket

    #         except Exception as e:
    #             print(f"Error in accept: {e}")



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
            print("客户端，尝试发送第一次握手")
            self.print_header(syn_header)
            self.socket.sendto(syn_header.to_bytes(), self.proxy_server_addr)
            time.sleep(3)
            print("客户端，接收第二次握手")
            data, server_addr = self.socket.recvfrom(1024)
            syn_ack_header = RDTHeader().from_bytes(data)
            #server_addr = self.create_address(syn_ack_packet.Source_address)
            # print("作为客户端，接收第二次握手")
            if syn_ack_header.SYN == 1 and syn_ack_header.ACK == 1 and syn_ack_header.ACK_num == self.seq_num + 1:
                self.ack_num = syn_ack_header.SEQ_num + 1
                #server_addr = address
                self.target_address = self.list_to_tuple(syn_ack_header.Source_address)
                # addr = self.socket.getsockname()
                connection_key = (self.address[0], self.address[1], address[0], address[1])
                print("客户端socket的key为：", connection_key)
                self.connections[connection_key] = self # 存下socket
                print("客户端self.connections大小为", len(self.connections))
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
        self.client_sending = threading.Thread(target=self.client_sender, args=(data, test_case))
        self.client_receiving = threading.Thread(target=self.client_receiver)
        self.client_sending.start()
        self.client_receiving.start()
        self.client_sending.join()
        # print("self.client_sending.join()")
        self.client_receiving.join()
        # print("self.client_receiving.join()")
    
    # def send(self, data=None, tcpheader=None, test_case=0):
    #     """
    #     RDT可以使用此函数将指定的数据发送到已经建立可靠连接的目标。请注意，在计算之前，
    #     应该计算指定数据的相应CHECKSUM。此外，此函数应该在发送阶段实现流量控制。此外，
    #     当要发送的数据过大时，此函数应该能够将数据分成多个块，并以流水线方式发送到目标。
        
    #     params:
    #         data:       将被发送的数据。
    #         tcpheader:  包括SYN, ACK, FIN, CHECKSUM等。在需要时使用此属性。
    #         test_case:  表示本实验中将使用的测试案例。
    #     """
    #     try:
    #         # 第一次握手：发送SYN请求
    #         self.seq_num = random.randint(0, 2 ** 32 - 1)
    #         syn_header = RDTHeader(SYN=1, SEQ_num=self.seq_num)
    #         syn_header.Source_address = self.tuple_to_list(self.address)
    #         syn_header.Target_address = self.tuple_to_list(self.target_address)
    #         self.print_header(syn_header)
    #         self.socket.sendto(syn_header.to_bytes(), self.proxy_server_addr)

    #         # 等待接收第二次握手的SYN-ACK包
    #         print("客户端等待接收第二次握手")
    #         data, server_addr = self.socket.recvfrom(1024)
    #         syn_ack_header = RDTHeader().from_bytes(data)
    #         if syn_ack_header.SYN == 1 and syn_ack_header.ACK == 1 and syn_ack_header.ACK_num == self.seq_num + 1:
    #             self.ack_num = syn_ack_header.SEQ_num + 1
    #             self.target_address = self.list_to_tuple(syn_ack_header.Source_address)

    #             # 发送第三次握手的ACK确认
    #             ack_header = RDTHeader(ACK=1, ACK_num=syn_ack_header.SEQ_num + 1)
    #             ack_header.Source_address = self.tuple_to_list(self.address)
    #             ack_header.Target_address = self.tuple_to_list(self.target_address)
    #             self.print_header(ack_header)
    #             self.socket.sendto(ack_header.to_bytes(), self.proxy_server_addr)
    #             print("客户端成功建立连接")
    #         else:
    #             print("收到无效的握手响应，连接失败")

    #     except Exception as e:
    #         print(f"Error in send: {e}")


    def recv(self):
        """
        You should implement the basic logic for receiving data in this function, and 
        verify the data. When corrupted or missing data packets are detected, a request 
        for retransmission should be sent to the other party.
        
        This function should be bolcking.
        """
        #############################################################################
        while True:
            print("Receiver waiting for data...")
            print("当前接收地址为", self.address)
            print("接收时服务器监听地址为", self.socket.getsockname())
            data, _ = self.socket.recvfrom(1024)
            print("已接收数据包!!!")
            print(data)
            # 解析header，获取目标地址
            packet = RDTHeader().from_bytes(data)
            client_address = self.list_to_tuple(packet.Source_address)
            dest_address = self.list_to_tuple(packet.Target_address)
            # 得到四元组
            key = (client_address[0], client_address[1], dest_address[0], dest_address[1])
            print("接收端所有储存的socket的地址")
            for x in self.connections:
                print(x)
            print("输出完毕，数量为", len(self.connections))
            test_case = packet.test_case
            print("目标地址为：")
            print(client_address)
            if key in self.connections:
                conn = self.connections[key]  # conn为对应的套接字
                print("找到对应的套接字, 对应的四元组为", key)
            else:
                # 如果找不到对应的套接字，则忽略该消息
                print("找不到对应的套接字")
                # continue
                break
            print("已解析checksum")
            print(packet.CHECKSUM)
            checksum_local = conn.cal_checksum(packet.to_bytes())
            print(checksum_local)
            if checksum_local == packet.CHECKSUM:
                print("checksum正确")
                print(packet.SEQ_num + 1)
                print(conn.ack_num)
                # if packet.SEQ_num + 1 < self.ack_num:#该包其实已经正确收到
                #     continue
                if packet.SEQ_num + 1 <= conn.ack_num:#判断紧接或已经正确收到
                    with conn.lock:
                        conn.ack_num = (packet.SEQ_num + 1) % (2 ** 32)
                        ack_header = RDTHeader(ACK=1, SEQ_num=conn.seq_num, ACK_num=conn.ack_num, RWND=4-len(self.receiver_buffer))
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
                    break
                    #直接输出data并发送ACK包，检查缓冲区是否存在紧接
                else:
                    print(len(self.receiver_buffer))
                    if len(self.receiver_buffer) < 5:#判断缓冲区是否未满
                        with self.lock:
                            self.receiver_buffer[packet.SEQ_num] = (packet)
                        #未满，存入缓冲区
                    else:
                        # continue
                        break
                        #已满，丢弃，不发送NAK包
            else:
                print("checksum不正确")
                # 错误数据，发送NAK包并丢弃
                with self.lock:
                    nak_header = RDTHeader(ACK=0, SEQ_num=self.seq_num, ACK_num=self.ack_num)
                    nak_header.Source_address = self.tuple_to_list(self.address)
                    nak_header.Target_address = self.tuple_to_list(client_address)
                    nak_header.test_case = test_case
                    self.print_header(nak_header)
                    self.socket.sendto(nak_header.to_bytes(), self.proxy_server_addr)
                    print("已请求重传")
        # self.socket.close()


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
        try:
            # 第一次挥手：发送FIN包
            fin_header = RDTHeader(FIN=1, SEQ_num=self.seq_num)
            fin_header.test_case = 21  # 假设用于测试的特定案例
            print("客户端发送FIN包开始关闭连接")
            self.print_header(fin_header)
            self.socket.sendto(fin_header.to_bytes(), self.proxy_server_addr)

            # 第二次挥手：接收ACK
            while True:
                print("客户端等待ACK响应")
                self.socket.settimeout(10)  # 设置超时为10秒
                try:
                    ack_data, _ = self.socket.recvfrom(1024)
                    ack_header = RDTHeader().from_bytes(ack_data)
                    print("收到ACK包：", ack_data)
                    if ack_header.ACK == 1 and ack_header.ACK_num == self.seq_num + 1:
                        print("收到对FIN的确认ACK")

                        # 第三次挥手：接收对方的FIN
                        print("客户端等待对方的FIN包")
                        fin_data, _ = self.socket.recvfrom(1024)
                        fin_ack_header = RDTHeader().from_bytes(fin_data)
                        print("收到FIN包：", fin_data)
                        if fin_ack_header.FIN == 1:
                            self.ack_num = fin_ack_header.SEQ_num + 1
                            print("收到对方的FIN包")

                            # 第四次挥手：发送最后一个ACK
                            final_ack_header = RDTHeader(ACK=1, ACK_num=self.ack_num)
                            final_ack_header.test_case = 21
                            print("发送最后一个ACK确认")
                            self.print_header(final_ack_header)
                            self.socket.sendto(final_ack_header.to_bytes(), self.proxy_server_addr)
                            print("四次挥手完成，连接关闭")
                            break
                    else:
                        print("未收到有效的ACK响应，挥手失败")
                        break
                except Exception as e:
                    print(f"Error in close: {e}")
                    print("等待ACK响应超时，重传FIN包")
                    self.socket.sendto(fin_header.to_bytes(), self.proxy_server_addr)

        except Exception as e:
            print(f"关闭连接时发生异常: {e}")
            raise e
        finally:
            # 关闭套接字
            self.socket.close()
            print("套接字已关闭")

        
    def close_server(self):
        """
        Close current RDT connection.
        You should follow the 4-way-handshake, and then the RDT connection will be terminated.
        """
        try:
            while True:
                try:
                    # 接收客户端的FIN包
                    print("服务端等待客户端的FIN包")
                    fin_data, client_address = self.socket.recvfrom(1024)
                    print("收到FIN包：", fin_data)
                    fin_header = RDTHeader().from_bytes(fin_data)
                    print("收到FIN包：", fin_data)
                    if fin_header.FIN == 1:
                        self.ack_num = fin_header.SEQ_num + 1

                        # 第二次挥手：发送ACK确认
                        ack_header = RDTHeader(ACK=1, ACK_num=self.ack_num)
                        print("发送ACK包确认客户端的FIN")
                        self.print_header(ack_header)
                        self.socket.sendto(ack_header.to_bytes(), self.proxy_server_addr)

                        # 日志记录
                        print("服务端发送ACK包：", ack_header.to_bytes())

                        # 第三次挥手：发送FIN包
                        fin_ack_header = RDTHeader(FIN=1, SEQ_num=self.seq_num)
                        print("服务端发送FIN包")
                        self.print_header(fin_ack_header)
                        self.socket.sendto(fin_ack_header.to_bytes(), self.proxy_server_addr)

                        # 第四次挥手：接收客户端的ACK
                        self.socket.settimeout(10)  # 设置超时为10秒
                        try:
                            final_ack_data, _ = self.socket.recvfrom(1024)
                            final_ack_header = RDTHeader().from_bytes(final_ack_data)
                            if final_ack_header.ACK == 1 and final_ack_header.ACK_num == self.seq_num + 1:
                                print("收到客户端的最后一个ACK，连接关闭")
                                break
                        except Exception as e:
                            print("等待最后一个ACK响应超时，连接关闭失败")
                            break
                    else:
                        print("收到无效的FIN包，继续等待")
                except Exception as e:
                    print("等待客户端的FIN包超时，重试")
        except Exception as e:
            print(f"关闭连接时发生异常: {e}")
            raise e
        finally:
            # 关闭套接字
            self.socket.close()
            print("套接字已关闭")


    # def close(self):
    #     # 发送 FIN 报文
    #     fin_packet = RDTHeader(FIN=1, SEQ_num=self.seq_num)
    #     self.socket.sendto(fin_packet.to_bytes(), self.target_address)
        
    #     # 等待接收服务器的 ACK 报文和 FIN 报文
    #     while True:
    #         try:
    #             data, addr = self.socket.recvfrom(1024)
    #             packet = RDTHeader.from_bytes(data)
                
    #             # 接收服务器的 ACK 报文
    #             if packet.ack == 1 and packet.ack_num == self.seq_num + 1:
    #                 print("Received ACK for FIN")
                    
    #             # 接收服务器的 FIN 报文
    #             if packet.fin == 1:
    #                 print("Received FIN from server")
                    
    #                 # 发送 ACK 报文确认
    #                 ack_packet = RDTHeader(ACK=1, ACK_num=self.ack_num)
    #                 self.socket.sendto(ack_packet.to_bytes(), self.target_address)
    #                 print("Sent ACK for server's FIN")
    #                 break
    #         except timeout:
    #             print("Timeout, resending FIN")
    #             self.socket.sendto(fin_packet.to_bytes(), self.target_address)
        
    #     # 关闭套接字
    #     self.socket.close()
    #     print("Connection closed")



    # def close(self):
    #     """
    #     Close current RDT connection.
    #     You should follow the 4-way-handshake, and then the RDT connection will be terminated.
    #     """
    #     #############################################################################
    #     #self.socket = socket(AF_INET, SOCK_DGRAM)
    #     #self.socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    #     # print(self.address)
    #     #self.socket.bind(self.address)                                      #
    #     try:
    #     # 第一次挥手：发送FIN包
    #         fin_header = RDTHeader(FIN=1, SEQ_num=self.seq_num)
    #         fin_header.Source_address = self.tuple_to_list(self.address)
    #         fin_header.Target_address = self.tuple_to_list(self.target_address)
    #         fin_header.test_case = 21  # 假设用于测试的特定案例
    #         print("客户端发送FIN包开始关闭连接")
    #         self.print_header(fin_header)
    #         self.socket.sendto(fin_header.to_bytes(), self.proxy_server_addr)

    #         # 第二次挥手：接收ACK
    #         print("客户端等待ACK响应")
    #         ack_data, _ = self.socket.recvfrom(1024)
    #         ack_header = RDTHeader().from_bytes(ack_data)
    #         if ack_header.ACK == 1 and ack_header.ACK_num == self.seq_num + 1:
    #             print("收到对FIN的确认ACK")

    #             # 第三次挥手：接收对方的FIN
    #             print("客户端等待对方的FIN包")
    #             fin_data, _ = self.socket.recvfrom(1024)
    #             fin_ack_header = RDTHeader().from_bytes(fin_data)
    #             if fin_ack_header.FIN == 1:
    #                 self.ack_num = fin_ack_header.SEQ_num + 1
    #                 print("收到对方的FIN包")

    #                 # 第四次挥手：发送最后一个ACK
    #                 final_ack_header = RDTHeader(ACK=1, ACK_num=self.ack_num)
    #                 final_ack_header.Source_address = self.tuple_to_list(self.address)
    #                 final_ack_header.Target_address = self.tuple_to_list(self.target_address)
    #                 final_ack_header.test_case = 21
    #                 print("发送最后一个ACK确认")
    #                 self.print_header(final_ack_header)
    #                 self.socket.sendto(final_ack_header.to_bytes(), self.proxy_server_addr)
    #                 print("四次挥手完成，连接关闭")
    #         else:
    #             print("未收到有效的ACK响应，挥手失败")

    #     except Exception as e:
    #         print(f"关闭连接时发生异常: {e}")
    #         raise e
    #     finally:
    #         # 关闭套接字
    #         self.socket.close()
    #         print("套接字已关闭")
        #############################################################################
        # raise NotImplementedError()

    # def close(self):
    #     """
    #     关闭当前的RDT连接。应该遵循四次挥手，然后RDT连接将被终止。
    #     """
    #     try:
    #         # 第一次挥手：发送FIN包
    #         fin_header = RDTHeader(FIN=1, SEQ_num=self.seq_num)
    #         fin_header.Source_address = self.tuple_to_list(self.address)
    #         fin_header.Target_address = self.tuple_to_list(self.target_address)
    #         self.print_header(fin_header)
    #         self.socket.sendto(fin_header.to_bytes(), self.proxy_server_addr)

    #         # 等待接收第二次挥手的ACK确认
    #         print("客户端等待接收对FIN的ACK确认")
    #         ack_data, _ = self.socket.recvfrom(1024)
    #         ack_header = RDTHeader().from_bytes(ack_data)
    #         if ack_header.ACK == 1 and ack_header.ACK_num == self.seq_num + 1:
    #             print("收到对FIN的ACK确认")

    #             # 等待接收对方的FIN包
    #             print("客户端等待对方的FIN包")
    #             fin_data, _ = self.socket.recvfrom(1024)
    #             fin_ack_header = RDTHeader().from_bytes(fin_data)
    #             if fin_ack_header.FIN == 1:
    #                 self.ack_num = fin_ack_header.SEQ_num + 1
    #                 print("收到对方的FIN包")

    #                 # 发送最后一个ACK确认
    #                 final_ack_header = RDTHeader(ACK=1, ACK_num=self.ack_num)
    #                 final_ack_header.Source_address = self.tuple_to_list(self.address)
    #                 final_ack_header.Target_address = self.tuple_to_list(self.target_address)
    #                 self.print_header(final_ack_header)
    #                 self.socket.sendto(final_ack_header.to_bytes(), self.proxy_server_addr)
    #                 print("四次挥手完成，连接已关闭")
    #         else:
    #             print("未收到有效的ACK确认，挥手失败")

    #     except Exception as e:
    #         print(f"Error in close: {e}")


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
        """ip, port = ip_port_tuple
        ip_parts = list(map(int, ip.split('.')))
        return ip_parts + [port]"""
        # 将地址改成header需要的列表形式
        temp = ip_port_tuple[0].split(".")
        temp1 = temp[0]
        temp2 = temp[1]
        temp3 = temp[2]
        temp4 = temp[3]
        port = ip_port_tuple[1]
        header_address = [int(temp1), int(temp2), int(temp3), int(temp4), port]
        return header_address

    def list_to_tuple(self, ip_port_list):
        """ip_parts = ip_port_list[:4]
        port = ip_port_list[4]
        ip = '.'.join(map(str, ip_parts))
        return (ip, port)"""
        # 将地址组合成需要的元组形式
        temp1 = ip_port_list[0]
        temp2 = ip_port_list[1]
        temp3 = ip_port_list[2]
        temp4 = ip_port_list[3]
        port = ip_port_list[4]  # 端口号
        ip = str(temp1) + "." + str(temp2) + "." + str(temp3) + "." + str(temp4)  # 目标ip地址
        address = (ip, port)  # 目标地址
        return address

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
            print("已接收到ACK数据包\n")
            ack_packet = RDTHeader().from_bytes(data)
            addr = self.list_to_tuple(ack_packet.Source_address)
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
        while  data  or self.sender_buffer:
            print(type(data))
            print("data_len:" + str(data_len))
            print("sender_buffer:")
            print(self.sender_buffer)
            if len(self.sender_buffer) < 5 and data and self.rwnd > 0:
                chunk = data[:256]  # 最大256字节的数据块
                data = data[256:]
                packet = RDTHeader(SEQ_num=self.seq_num, ACK_num=self.ack_num, LEN=data_len, CHECKSUM=0, PAYLOAD=chunk.decode())
                packet.Source_address = self.tuple_to_list(self.address)
                packet.Target_address = self.tuple_to_list(self.target_address)
                packet.CHECKSUM = self.cal_checksum(packet.to_bytes())
                print("已计算checksum")
                packet.test_case = test_case
                with self.lock:
                    self.sender_buffer[self.seq_num] = (packet, time.time())
                    self.print_header(packet)
                    self.socket.sendto(packet.to_bytes(), self.target_address)
                    print("发送目标地址为", self.target_address)
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
                            # self.print_heaader(value[0])
                            self.socket.sendto(value[0].to_bytes(), self.target_address)
                            print("超时重发一块数据:", key)
            break
            # time.sleep(5)
        self.sending_finish = True
        
    # def client_sender(self, data, test_case):
    #         data_len = len(data) # 文件总长度
    #         for i in range(0, len(data), 1024):
    #             chunk = data[i:i+1024]
    #             packet = RDTHeader(SEQ_num=self.seq_num, ACK_num=self.ack_num, LEN=data_len, CHECKSUM=0, PAYLOAD=chunk.decode())
    #             packet.Source_address = self.tuple_to_list(self.address)
    #             packet.Target_address = self.tuple_to_list(self.target_address)
    #             packet.PAYLOAD = chunk
    #             packet.CHECKSUM = self.cal_checksum(packet.to_bytes())
    #             packet.test_case = test_case
    #             self.print_header(packet)
    #             self.socket.sendto(packet.to_bytes(), self.proxy_server_addr)
    #             self.seq_num += len(chunk)
    #             time.sleep(0.1)  # Simulate network delay
    #     # print("set self.sending_finish = True")

    def server_getdata(self):

        # print("获取数据")
        if len(self.finished_data) > 0:
            data = self.finished_data.pop()
        else:
            data = ""
        return data


# import random
# import socket
# import time
# import threading
# from collections import OrderedDict
# from Header import RDTHeader
# from socket import AF_INET, SOCK_DGRAM, SOL_SOCKET, SO_REUSEADDR


# class RDTSocket():
#     def __init__(self) -> None:
#         self.proxy_server_addr = None
#         self.address = None
#         self.socket = socket.socket(AF_INET, SOCK_DGRAM)
#         self.connections = {}

#         # Server-specific attributes
#         self.count = 0
#         self.peer_info = {}

#         # Client and server connection-specific attributes
#         self.seq_num = 0
#         self.ack_num = 0

#         # Client-specific attributes
#         self.target_address = None
#         self.client_receiving = None
#         self.client_sending = None
#         self.lock = threading.Lock()
#         self.sender_buffer = {}
#         self.sending_finish = False
#         self.rwnd = 4

#         # Server connection-specific attributes
#         self.receiver_buffer = {}
#         self.receiver_window = None
#         self.finished_seq_num = None
#         self.data_buffer = ''
#         self.finished_data = []

#     def bind(self, address: (str, int)):
#         try:
#             self.socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
#             self.socket.bind(address)
#             self.address = address
#             print("Socket bound successfully:", address)
#         except OSError as e:
#             print("Error binding socket:", str(e))

#     def accept(self):
#         while True:
#             try:
#                 data, _ = self.socket.recvfrom(1024)
#                 header = RDTHeader().from_bytes(data)
#                 client_address = self.list_to_tuple(header.Source_address)
#                 print("Received data from:", header.Source_address)

#                 if header.SYN == 1:
#                     print("Server received SYN, first handshake")
#                     if client_address not in self.peer_info:
#                         seq_num = random.randint(0, 2 ** 32 - 1)
#                         ack_num = header.SEQ_num + 1
#                         self.peer_info[client_address] = (seq_num, ack_num, self.address[1])
#                         self.count += 1
#                     else:
#                         seq_num = self.peer_info[client_address][0]
#                         ack_num = self.peer_info[client_address][1]

#                     syn_ack_header = RDTHeader(SYN=1, ACK=1, SEQ_num=seq_num, ACK_num=ack_num)
#                     syn_ack_header.Source_address = self.tuple_to_list((self.address[0], self.peer_info[client_address][2]))
#                     syn_ack_header.Target_address = self.tuple_to_list(client_address)
#                     syn_ack_header.test_case = 20
#                     self.socket.sendto(syn_ack_header.to_bytes(), self.proxy_server_addr)

#                 elif header.ACK == 1 and client_address in self.peer_info and header.ACK_num - 1 == self.peer_info[client_address][0]:
#                     print("Server received ACK, third handshake")
#                     conn_socket = RDTSocket()
#                     conn_socket.address = (self.address[0], self.peer_info[client_address][2])
#                     conn_socket.proxy_server_addr = self.proxy_server_addr
#                     conn_socket.seq_num = self.peer_info[client_address][0]
#                     conn_socket.ack_num = self.peer_info[client_address][1]

#                     key = (client_address[0], client_address[1], self.address[0], self.peer_info[client_address][2])
#                     self.connections[key] = conn_socket
#                     return conn_socket
#             except Exception as e:
#                 print(f"Error in accept: {e}")

#     def connect(self, address: (str, int)):
#         try:
#             self.seq_num = random.randint(0, 2 ** 32 - 1)
#             syn_header = RDTHeader(SYN=1, SEQ_num=self.seq_num)
#             syn_header.Source_address = self.tuple_to_list(self.address)
#             syn_header.Target_address = self.tuple_to_list(address)
#             syn_header.test_case = 20
#             self.socket.sendto(syn_header.to_bytes(), self.proxy_server_addr)

#             data, server_addr = self.socket.recvfrom(1024)
#             syn_ack_header = RDTHeader().from_bytes(data)
#             if syn_ack_header.SYN == 1 and syn_ack_header.ACK == 1 and syn_ack_header.ACK_num == self.seq_num + 1:
#                 self.ack_num = syn_ack_header.SEQ_num + 1
#                 self.target_address = self.list_to_tuple(syn_ack_header.Source_address)
#                 connection_key = (self.address[0], self.address[1], address[0], address[1])
#                 self.connections[connection_key] = self

#                 ack_header = RDTHeader(ACK=1, ACK_num=syn_ack_header.SEQ_num + 1)
#                 ack_header.Source_address = self.tuple_to_list(self.address)
#                 ack_header.Target_address = self.tuple_to_list(address)
#                 ack_header.test_case = 20
#                 self.socket.sendto(ack_header.to_bytes(), self.proxy_server_addr)
#             else:
#                 print("Invalid handshake response")
#         except Exception as e:
#             print(f"Error in connect: {e}")

#     def send(self, data=None, tcpheader=None, test_case=0):
#         try:
#             data = data.encode()
#             self.client_sending = threading.Thread(target=self.client_sender, args=(data, test_case))
#             self.client_receiving = threading.Thread(target=self.client_receiver)
#             self.client_sending.start()
#             self.client_receiving.start()
#             self.client_sending.join()
#             self.client_receiving.join()
#         except Exception as e:
#             print(f"Error in send: {e}")

#     def recv(self):
#         while True:
#             try:
#                 print("Receiver waiting for data...")
#                 data, _ = self.socket.recvfrom(1024)
#                 packet = RDTHeader().from_bytes(data)
#                 client_address = self.list_to_tuple(packet.Source_address)
#                 dest_address = self.list_to_tuple(packet.Target_address)
#                 key = (client_address[0], client_address[1], dest_address[0], dest_address[1])

#                 if key in self.connections:
#                     conn = self.connections[key]
#                 else:
#                     print("No corresponding socket found")
#                     break

#                 if conn.cal_checksum(packet.to_bytes()) == packet.CHECKSUM:
#                     if packet.SEQ_num + 1 <= conn.ack_num:
#                         with conn.lock:
#                             conn.ack_num = (packet.SEQ_num + 1) % (2 ** 32)
#                             ack_header = RDTHeader(ACK=1, SEQ_num=conn.seq_num, ACK_num=conn.ack_num, RWND=4-len(self.receiver_buffer))
#                             ack_header.Source_address = self.tuple_to_list(self.address)
#                             ack_header.Target_address = self.tuple_to_list(client_address)
#                             ack_header.test_case = packet.test_case
#                             self.socket.sendto(ack_header.to_bytes(), self.proxy_server_addr)
#                         self.data_buffer += packet.PAYLOAD
#                         if len(self.data_buffer) == packet.LEN:
#                             self.finished_data.append(self.data_buffer)
#                             self.data_buffer = ''
#                         for key, value in self.receiver_buffer.items():
#                             if value.SEQ_num + 1 == conn.ack_num:
#                                 with self.lock:
#                                     conn.ack_num = (value.SEQ_num + 1) % (2 ** 32)
#                                     ack_header = RDTHeader(ACK=1, SEQ_num=conn.seq_num, ACK_num=conn.ack_num, RWND=4-len(self.receiver_buffer))
#                                     ack_header.Source_address = self.tuple_to_list(self.address)
#                                     ack_header.Target_address = self.tuple_to_list(client_address)
#                                     ack_header.test_case = value.test_case
#                                     self.socket.sendto(ack_header.to_bytes(), self.proxy_server_addr)
#                                     del self.receiver_buffer[key]
#                                 self.data_buffer += value.PAYLOAD
#                                 if len(self.data_buffer) == packet.LEN:
#                                     self.finished_data.append(self.data_buffer)
#                                     self.data_buffer = ''
#                     else:
#                         if len(self.receiver_buffer) < 5:
#                             with self.lock:
#                                 self.receiver_buffer[packet.SEQ_num] = packet
#             except Exception as e:
#                 print(f"Error in recv: {e}")

#     def close(self):
#         try:
#             fin_header = RDTHeader(FIN=1, SEQ_num=self.seq_num)
#             fin_header.Source_address = self.tuple_to_list(self.address)
#             fin_header.Target_address = self.tuple_to_list(self.target_address)
#             fin_header.test_case = 21
#             self.socket.sendto(fin_header.to_bytes(), self.proxy_server_addr)

#             ack_data, _ = self.socket.recvfrom(1024)
#             ack_header = RDTHeader().from_bytes(ack_data)
#             if ack_header.ACK == 1 and ack_header.ACK_num == self.seq_num + 1:
#                 fin_data, _ = self.socket.recvfrom(1024)
#                 fin_ack_header = RDTHeader().from_bytes(fin_data)
#                 if fin_ack_header.FIN == 1:
#                     self.ack_num = fin_ack_header.SEQ_num + 1
#                     final_ack_header = RDTHeader(ACK=1, ACK_num=self.ack_num)
#                     final_ack_header.Source_address = self.tuple_to_list(self.address)
#                     final_ack_header.Target_address = self.tuple_to_list(self.target_address)
#                     final_ack_header.test_case = 21
#                     self.socket.sendto(final_ack_header.to_bytes(), self.proxy_server_addr)
#         except Exception as e:
#             print(f"Error in close: {e}")

#     @staticmethod
#     def list_to_tuple(self):
#         try:
#             final_ack_header = RDTHeader(ACK=1, ACK_num=self.ack_num)
#             final_ack_header.Source_address = self.tuple_to_list(self.address)
#             final_ack_header.Target_address = self.tuple_to_list(self.target_address)
#             final_ack_header.test_case = 21  # 假设用于测试的特定案例
#             print("客户端发送最后的ACK包")
#             self.print_header(final_ack_header)
#             self.socket.sendto(final_ack_header.to_bytes(), self.proxy_server_addr)
#             print("连接已成功关闭")

#                 # 关闭套接字
#             self.socket.close()

#         except Exception as e:
#                 print(f"Error in close: {e}")

#         #############################################################################

#     # Helper functions
#     def tuple_to_list(self, tup):
#         return [tup[0], tup[1]]

#     def list_to_tuple(self, lst):
#         return (lst[0], lst[1])

#     def print_header(self, header):
#         print("Header Info: ", header.__dict__)

#     def cal_checksum(self, data):
#         return sum(data) % 256  # Example checksum calculation

#     def client_sender(self, data, test_case):
#         for i in range(0, len(data), 1024):
#             chunk = data[i:i+1024]
#             packet = RDTHeader(SEQ_num=self.seq_num, test_case=test_case)
#             packet.Source_address = self.tuple_to_list(self.address)
#             packet.Target_address = self.tuple_to_list(self.target_address)
#             packet.PAYLOAD = chunk
#             packet.CHECKSUM = self.cal_checksum(packet.to_bytes())
#             self.print_header(packet)
#             self.socket.sendto(packet.to_bytes(), self.proxy_server_addr)
#             self.seq_num += len(chunk)
#             time.sleep(0.1)  # Simulate network delay

#     def client_receiver(self):
#         while not self.sending_finish:
#             try:
#                 data, _ = self.socket.recvfrom(1024)
#                 packet = RDTHeader().from_bytes(data)
#                 if packet.ACK == 1 and packet.ACK_num > self.ack_num:
#                     self.ack_num = packet.ACK_num
#                     print("客户端接收到ACK包:", self.ack_num)
#                 elif packet.ACK == 0:
#                     print("客户端接收到NAK包，重传数据")
#                     # Handle retransmission logic here
#             except Exception as e:
#                 print(f"Error in client_receiver: {e}")

#     def handle_client(self, client_address):
#         # Handle client communication in a separate thread
#         pass
