import Packet
import sys
import pickle

filename = 'C:\\Users\\kylep\\OneDrive\\Desktop\\School\\message.txt'

try:
    file = open(filename, 'rb')
except IOError:
    print("--ERROR OPENING FILE--")


packets = []

data = file.read(1024)

#data = b'\xe6\x66\xd5\x55\x00\x11\x22\x33\xe6\x66\xd5\x55\x00\x11\x22\x33'
print(sys.getsizeof(data))
p = Packet.Packet(0, data)
#print(hex(p.checksum))
pkl = pickle.dumps(p)
print(sys.getsizeof(pkl))