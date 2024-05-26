# note：解释代码基本流程

### 1. receiver_sock（服务器）:
  1. bind("127.0.0.1", 12349)  *如果经过代理服务器，则需要具体的本地ip，下同*
  2. accept()  等待连接
### 2. sender_sock（客户端）: 
  1. bind("127.0.0.1", 12344)  
  2. connect("127.0.0.1", 12349)  发起连接请求
### 3. 建立连接（三次握手）*该部分可能需要修改*
  1. receiver_sock.accept()会创建conn_server_sock用于传输
  2. conn_server_sock.bind("127.0.0.1", 12021)
  3. 第二次握手由conn_server_sock.send()，客户端会记录conn_server_sock的address作为新的连接对象
### 4. sender_sock（客户端）: 
  1. send(data)
### 5. conn_server_sock（服务器）:
  1. recv()
