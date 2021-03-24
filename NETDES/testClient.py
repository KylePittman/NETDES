import socket
import pickle
import Packet

address = ('localhost', 777)
print(f"--Opening Socket Port: {address}--")

serverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
serverSocket.bind(address)

data, _ = serverSocket.recvfrom(2048)
packet = pickle.loads(data)
print(data)