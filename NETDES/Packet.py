

class Packet:
    ID = -1
    checksum = b'FFFFFFFF'
    data =b''

    def __init__(self, ID, data):
        self.ID = ID
        self.data = data
        self.generateChecksum()

    def addBytes(self, a, b):
        sum = a + b
        return (sum & 0xffff) + (sum >> 16)

    def generateChecksum(self):
        sum = 0

        for i in range(0, len(self.data), 2):
            #Read in two bytes of data as one 16 bit segment
            twoBytesOfData = (self.data[i] << 8) + self.data[i+1]

            #Use add function to add current segment to sum
            sum = self.addBytes(sum, twoBytesOfData)
        #complement the sum and ensure it 16 bits long
        self.checksum = ~sum & 0xffff
