import socket
import threading
from collections import OrderedDict
from socket import *
from Header import RDTHeader
import random
import time


class RDTSocket():
    def __init__(self) -> None:
        """
        You shold define necessary attributes in this function to initialize the RDTSocket
        """
        #############################################################################
        # TODO: NECESSARY ATTRIBUTES HERE                                           #
        self.socket = socket(AF_INET, SOCK_DGRAM)
        self.connected = False
        self.lock = None
        self.client_sockets = {}
        self.send_buffer = {}  # 发送缓冲区
        self.recv_buffer = {}  # 接收缓冲区
        self.connections = {}
        self.proxy_server_addr = None
        self.seq_num = 0  # 下一个待发送数据包的序列号
        self.ack_num = 0  # 最新确认的序列号
        self.cwnd = 1024
        self.rwnd = 1024
        self.timeout = 1.0  # 超时时间(秒)
        # self.local_addr = self.socket.getsockname()
        self.remote_addr = None
        #############################################################################
        
        #############################################################################
        # TODO: YOUR CODE HERE                                                      #
        #############################################################################
        pass
    
    def bind(self, address: (str, int)): # type: ignore
        """
        When trying to establish a connection. The socket must be bound to an address 
        and listening for connections. address is the address bound to the socket on 
        the other end of the connection.

        This function should be blocking. 
        
        params: 
            address:    Target IP address and its port
        """
        #############################################################################
        # TODO: YOUR CODE HERE                                                      #
        if self.connected:
            raise Exception("Socket already connected, could not bind again.")
        try:
            self.socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            self.socket.bind(address)
            print("Socket bound successfully.")
        except OSError as e:
            print("Error binding socket:", str(e))
        #############################################################################
        #raise NotImplementedError()

    # 服务器accept
    def accept(self): #-> RDTSocket: # type: ignore
        """
        When using this SOCKET to create an RDT SERVER, it should accept the connection
        from a CLIENT. After that, an RDT connection should be established.
        Please note that this function needs to support multithreading and be able to 
        establish multiple socket connections. Messages from different sockets should 
        be isolated from each other, requiring you to multiplex the data received at 
        the underlying UDP.
        """
        #############################################################################
        # TODO: YOUR CODE HERE                                                      #
        """client_socket, client_addr = self.socket.accept()
        with self.lock:
            self.client_sockets[client_addr] = client_socket
        return RDTSocket(client_socket)"""
        # 接收连接请求
        data, addr = self.socket.recvfrom(1024)
        header = RDTHeader().from_bytes(data) # 将解析后的数据存储在header对象中
        print("作为服务器，接收第一次握手")
        self.lock = threading.Lock()
        # 如果是SYN请求, 三次握手
        if header.SYN == 1:
            # 创建新连接
            with self.lock:
                # print("in lock")
                conn = RDTSocket()
                # conn.lock = threading.Lock()
                conn_port = 12021
                conn.bind(("127.0.0.1", conn_port))
                conn.seq_num = random.randint(0, 2 ** 32 - 1)
                conn.ack_num = header.SEQ_num + 1
                # with self.lock:
                self.connections[addr] = conn
                #conn.server_addr = addr

            # 发送SYN-ACK响应
            syn_ack_header = RDTHeader(SYN=1, ACK=1, SEQ_num=conn.seq_num, ACK_num=conn.ack_num)
            conn.socket.sendto(syn_ack_header.to_bytes(), addr)
            print("作为服务器，发送第二次握手")
            # 等待ACK
            data, addr = conn.socket.recvfrom(1024)
            header = RDTHeader().from_bytes(data) # 将解析后的数据存储在header对象中
            print("作为服务器，接收第三次握手")
            # 如果收到ACK
            if header.ACK == 1  and header.ACK_num == conn.seq_num + 1:
                # 连接建立成功
                conn.connected = True
                print("作为服务器，建立连接成功")
                return conn

        raise Exception("无法建立连接")
        #############################################################################
        #raise NotImplementedError()

    # 客户端发起connect
    def connect(self, address: (str, int)): # type: ignore
        """
        When using this SOCKET to create an RDT client, it should send the connection
        request to target SERVER. After that, an RDT connection should be established.
        
        params:
            address:    Target IP address and its port
        """
        #############################################################################
        # TODO: YOUR CODE HERE                                                      #
        try:
            # 实现三次握手
            #syn_packet = RDTHeader(syn=1)
            #self.socket.sendto(syn_packet.to_bytes(), address)

            # 第一次握手：客户端发送SYN请求
            self.seq_num = random.randint(0, 2 ** 32 - 1)
            syn_header = RDTHeader(SYN=1, SEQ_num=self.seq_num)
            self.socket.sendto(syn_header.to_bytes(), address)
            print("作为客户端，发送第一次握手")

            print("要发送的包：")
            print(syn_header.test_case)
            print(syn_header.Source_address)
            print(syn_header.Target_address)
            print(syn_header.SYN)
            print(syn_header.FIN)
            print(syn_header.ACK)
            print(syn_header.SEQ_num)
            print(syn_header.ACK_num)
            print(syn_header.LEN)
            print(syn_header.CHECKSUM)
            print(syn_header.RWND)
            print(syn_header.Reserved)
            print(syn_header.PAYLOAD)
            print(syn_header.to_bytes())

            data, server_addr = self.socket.recvfrom(1024)
            syn_ack_packet = RDTHeader().from_bytes(data) # 将解析后的数据存储在syn_ack_packet对象中
            print("作为客户端，接收第二次握手")
            if syn_ack_packet.SYN == 1 and syn_ack_packet.ACK == 1 and syn_ack_packet.ACK_num == self.seq_num + 1:
                self.ack_num = syn_ack_packet.SEQ_num + 1
                self.server_addr = server_addr
                self.connections[server_addr] = self
                # 第三次握手：发送ACK确认
                ack_packet = RDTHeader(ACK=1, ACK_num=syn_ack_packet.SEQ_num + 1)
                self.socket.sendto(ack_packet.to_bytes(), server_addr)
                print("作为客户端，发送第三次握手")
                print("要发送的包：")
                print(ack_packet.test_case)
                print(syn_header.Source_address)
                print(syn_header.Target_address)
                print(syn_header.SYN)
                print(syn_header.FIN)
                print(syn_header.ACK)
                print(syn_header.SEQ_num)
                print(syn_header.ACK_num)
                print(syn_header.LEN)
                print(syn_header.CHECKSUM)
                print(syn_header.RWND)
                print(syn_header.Reserved)
                print(syn_header.PAYLOAD)
                print(syn_header.to_bytes())
                self.connected = True
                print("作为客户端，建立连接成功")
            else:
                # 握手失败
                print("收到无效的握手响应。握手失败。")
        except Exception as e:
            print("连接过程中出现异常:", str(e))
        #############################################################################
        #raise NotImplementedError()
    
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
        # TODO: YOUR CODE HERE                                                      #
        if not self.connected:
            raise ValueError("Socket is not connected")


        # 获取目标地址
        #target_addr = list(self.connections.keys())[0]
        target_addr = self.server_addr
        print("target pass")
        # 如果数据为空,发送tcpheader
        if data is None:
            checksum = 0
            print("数据为空，checksum为0")
            if tcpheader is not None:
                packet = tcpheader.to_bytes()
                self.socket.sendto(packet, target_addr)
                print("数据为空，已发送tcpheader")
            else:
                raise ValueError("At least one of 'data' or 'tcpheader' must be provided.")
        else:
            # 分段并发送数据
            data = data.encode() if isinstance(data, str) else "".encode()
            len_data = len(data)
            while data:
                chunk = data[:256]  # 最大256字节的数据块
                data = data[256:]
                # 计算checksum
                packet = RDTHeader(SEQ_num=self.seq_num, ACK_num=self.ack_num, LEN=len_data, CHECKSUM=0, PAYLOAD=chunk.decode(), RWND=self.rwnd)
                checksum = self.cal_checksum(packet.to_bytes())
                print("已计算checksum")
                packet.CHECKSUM = checksum
                packet.test_case = test_case
                # packet.Source_address = [127,0,0,1,12334]
                # packet.Target_address =[10,16,52,94,12345]
                self.send_buffer[self.seq_num] = (packet, time.time())

                print("要发送的包：")
                print(packet.test_case)
                print(packet.Source_address)
                print(packet.Target_address)
                print(packet.SYN)
                print(packet.FIN)
                print(packet.ACK)
                print(packet.SEQ_num)
                print(packet.ACK_num)
                print(packet.LEN)
                print(packet.CHECKSUM)
                print(packet.RWND)
                print(packet.Reserved)
                print(packet.PAYLOAD)
                print(packet.to_bytes())

                self.socket.sendto(packet.to_bytes(), target_addr)
                # print("经过代理服务器")
                # self.socket.sendto(packet.to_bytes(), ('10.16.52.94', 12345))
                self.seq_num = (self.seq_num + len(chunk) )% (2 ** 32)
                print("已发送一块数据")

        # 等待ACK并重传未确认的数据包
        while self.send_buffer:
            break
            self.handle_timeout()
            try:
                data, addr = self.socket.recvfrom(1024)
                print("已接收到ACK数据包\n")
                ack_packet = RDTHeader().from_bytes(data)
                # if not (ack_packet.ACK == 1 and ack_packet.ACK_num == (self.seq_num + 1) % (2 ** 32)):
                # if False:
                print(ack_packet.ACK_num)
                print(self.seq_num % (2 ** 32))
                if not (ack_packet.ACK == 1 and ack_packet.ACK_num == self.seq_num % (2 ** 32)):
                    print("需要重传")
                    self.handle_ack(ack_packet.ACK_num)
                    print(ack_packet.ACK_num)
                    self.socket.sendto(self.send_buffer[ack_packet.ACK_num][0].to_bytes(), target_addr)
                    print("已重传")
                else:
                    print(self.send_buffer)
                    self.send_buffer.pop(ack_packet.ACK_num-packet.LEN)
                    # 清楚收到的缓冲
            except BlockingIOError:
                continue
            if len(self.send_buffer) == 0:
                print("已重传完毕")
                break
        #self.ack_num = header.SEQ_num + 1
        #############################################################################
        #raise NotImplementedError()
    
    def recv(self):
        """
        You should implement the basic logic for receiving data in this function, and 
        verify the data. When corrupted or missing data packets are detected, a request 
        for retransmission should be sent to the other party.
        
        This function should be bolcking.
        """
        #############################################################################
        # TODO: YOUR CODE HERE                                                      #
        while True:
            if not self.connected:
                raise ValueError("Socket is not connected")
            recv_buffer = OrderedDict()  # 用有序字典保存接收到的分片
            total_len = 0  # 记录已接收数据的总长度
            while True:
                try:
                    # 接收数据包
                    data, addr = self.socket.recvfrom(1024)
                    print("已接收数据包")
                    print(data)
                    if data:
                        header = RDTHeader().from_bytes(data)

                        print("接受到的包：")
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

                        # header_checksum = header.CHECKSUM
                        # 检查校验和
                        payload_len = header.LEN
                        payload = data[42:42 + payload_len]
                        # print(header.CHECKSUM)
                        # header.CHECKSUM = 0
                        checksum = self.cal_checksum(header.to_bytes())

                        print("已解析checksum")
                        print(checksum)
                        print(header.CHECKSUM)
                        # 如果校验和正确
                        if checksum == header.CHECKSUM:
                            print("checksum正确")
                            # 发送ACK响应
                            ack_header = RDTHeader(ACK=1, SEQ_num=self.seq_num, ACK_num=header.SEQ_num + payload_len)
                            self.socket.sendto(ack_header.to_bytes(), addr)
                            print("已发送ACK响应")
                            # 更新确认号和序列号
                            self.ack_num = header.SEQ_num + payload_len
                            # self.seq_num = (self.seq_num + 1) % (2 ** 32)
                            # 更新已接收数据的总长度
                            total_len += len(header.PAYLOAD)
                            # 根据SEQ_num插入分片到接收缓冲区
                            # 将数据存储在recv_buffer中
                            self.recv_buffer[header.SEQ_num] = payload
                            # print(payload)
                            print("已存储进recv_buffer")
                            # 如果已接收数据长度等于LEN,说明已接收完整数据
                            if total_len == header.LEN:
                                print("已完整接收数据")
                                break
                        else:
                            print("checksum不正确")
                            # 发送NAK响应,丢弃该数据包,请求重传
                            nak_header = RDTHeader(ACK=0, SEQ_num=self.seq_num, ACK_num=header.SEQ_num)
                            self.socket.sendto(nak_header.to_bytes(), addr)
                            print("已请求重传")
                    else:
                        continue
                except BlockingIOError:
                    continue
                # 从recv_buffer中获取有序的数据
            ordered_data = b''
            for seq_num in sorted(self.recv_buffer.keys()):
                ordered_data += self.recv_buffer.pop(seq_num)
            print(ordered_data.decode())
            # print(self.recv_buffer)
            # 按SEQ_num顺序拼接数据
            # data = b''.join(chunk for _, chunk in sorted(recv_buffer.items()))
            print("receiver out\n")
            return ordered_data, addr
            # 返回数据负载
            #return payload.decode()
            """else:
                # 发送NAK响应,丢弃该数据包,请求重传
                nak_header = RDTHeader(ACK=0, SEQ_num=self.seq_num, ACK_num=header.SEQ_num)
                self.socket.sendto(nak_header.to_bytes(), addr)"""

            """self.buffer[header.SEQ_num] = header.PAYLOAD
            #self.ack_num = header.SEQ_num + len(header.PAYLOAD)
            return header.PAYLOAD"""
        ##############################################
        #raise NotImplementedError()
    
    
    # def close(self):
    #     """
    #     Close current RDT connection.
    #     You should follow the 4-way-handshake, and then the RDT connection will be terminated.
    #     """
    #     #############################################################################
    #     # TODO: YOUR CODE HERE                                                      #
    #     # 四次挥手
    #     self.connected = False
    #     self.socket.close()
    #     #############################################################################
    #     #raise NotImplementedError()

    def cal_checksum(self, data):
        #计算数据包的校验和
        # 1.将校验和字段先设置为0
        checksum = 0
        data =data[0:32]+b"\x00"+data[34:]
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

    def handle_timeout(self):
        # 超时重传
        # print("进入超时重传\n")
        current_time = time.time()
        for seq_num, (packet, send_time) in list(self.send_buffer.items()):
            if current_time - send_time > self.timeout:
                # 超时,重传数据包
                self.socket.sendto(packet.to_bytes(), self.server_addr)
                self.send_buffer[seq_num] = (packet, current_time)  # 更新发送时间
                print("已处理超时重传")

    def handle_ack(self, ack_num):
        # 处理接收的ACK
        acked_packets = []
        for seq_num in sorted(self.send_buffer.keys()):
            if seq_num < ack_num:
                acked_packets.append(seq_num)
            else:
                break

        # 从发送缓冲区中移除已确认的数据包
        for seq_num in acked_packets:
            self.send_buffer.pop(seq_num)

        # 更新ACK_num
        if acked_packets:
            self.ack_num = max(self.ack_num, max(acked_packets) + 1)
        print("已处理接收的ACK")

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
            # self.print_header(fin_header)
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
                            # self.print_header(final_ack_header)
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
                    break
        except Exception as e:
            print(f"关闭连接时发生异常: {e}")
            raise e
        finally:
            # 关闭套接字
            self.socket.close()
            print("套接字已关闭")