

class Packet:
    ID = -1
    checksum = b'FFFFFFFF'
    data =b''

    def __init__(self, ID, data):
        self.ID = ID
        self.data = data
        self.generateChecksum()

    def generateChecksum(self):
        self.checksum = 0
