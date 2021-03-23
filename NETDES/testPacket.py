import Packet

p = Packet.Packet(0,b'\xe6\x66\xd5\x55')
print(hex(p.checksum))