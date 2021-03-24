import tkinter as tk
import tkinter.filedialog as fd
import socket
import Packet
import pickle
import secrets


# Global Constants
BEGIN_TRANSMISSION = Packet.BEGIN_TRANSMISSION
SYN_ACK = Packet.SYN_ACK
END_TRANSMISSION = Packet.END_TRANSMISSION
PACKETSIZE = 1028
RECIEVESIZE = 2048
ACTIVE_TRANSMISSION = False
INTEGRITYCHECK = True
SEQUENCEID = True


# Global Variables
filename = ''
file = b''
socket_opened = False
serverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


# Simple class to store port and IP together
class Address:
    def __init__(self, IP, port):
        self.IP = IP
        self.port = int(port)


# Open socket to send/receive from
def openServer():
    global socket_opened

    if socket_opened:
        return
    address = parseAddressField(serverAddr)
    screenPrint(f"--Opening Socket Port: {address.port}--")
    serverSocket.bind((address.IP, address.port))
    serverSocket.settimeout(0.01)
    socket_opened = True


# Used to get user input from address field
def parseAddressField(field):
    temp = field.get().split(":")
    return Address(IP=temp[0], port=temp[1])


# Print Text to window
def screenPrint(msg):
    txt_output.insert(tk.END, f"{msg} \n")


# Main running function to receive transmitted data
def receive():
    if socket_opened:
        # wait to recieve a message
        try:
            data, clientAddr = serverSocket.recvfrom(RECIEVESIZE)
        except:
            data = None

        if data is not None:
            packet = pickle.loads(data)

            screenPrint('--Received Packet--')

            processPacket(packet, clientAddr)


    # This function calls itself every 100ms to allow tkinter's main function to run
    window.after(100, receive)

def initializeLink(clientAddr):
    global SEQUENCEID, ACK, filename, file, ACTIVE_TRANSMISSION
    ACK = secrets.token_hex(16).encode()
    ACTIVE_TRANSMISSION = True
    screenPrint("--Begin Transmission--")
    screenPrint(f"--ACK: {ACK}--")
    sendACK(clientAddr)
    file = b''
    filename = ""


def terminateLink(clientAddr):
    global ACTIVE_TRANSMISSION
    screenPrint("--End Transmission--")
    ACTIVE_TRANSMISSION = False
    writeFile()
    sendACK(clientAddr)

def sendNACK(clientAddr):
    nackPacket = Packet.Packet(b'\x00\x00\x00\x00')
    nackPacket.ID = SEQUENCEID
    serverSocket.sendto(pickle.dumps(nackPacket), clientAddr)

def sendACK(clientAddr):
    ackPacket = Packet.Packet(ACK)
    ackPacket.ID = SEQUENCEID
    serverSocket.sendto(pickle.dumps(ackPacket), clientAddr)

def processPacket(packet, clientAddr):
    global file, filename, SEQUENCEID

    checksum = packet.checksum
    packet.generateChecksum()

    if packet.checksum != checksum or SEQUENCEID == packet.ID:
        screenPrint(f"--CS: {checksum} | PCS: {packet.checksum} | SQ: {SEQUENCEID} | PID: {packet.ID}--")
        sendNACK(clientAddr)
        screenPrint("--Sent NACK--")
    else:
        if packet.data == SYN_ACK:
            initializeLink(clientAddr)
        elif packet.data == END_TRANSMISSION:
            terminateLink(clientAddr)
        elif filename == "":
            filename = packet.data.decode()
            screenPrint(f"--Filename: {filename}--")
            sendACK(clientAddr)
        else:
            screenPrint("--Loading File--")
            file = file + packet.data
            sendACK(clientAddr)

        SEQUENCEID = packet.ID
    return

# Writes the data transmitted to a file of the same name in the same working directory of the program
def writeFile():
    global filename
    path = fd.askdirectory() + '\\' + filename
    f = open(path, 'wb')
    f.write(file)
    f.close()
    filename = ''


# Set up window
window = tk.Tk()
serverAddr = tk.StringVar()

window.title("Server RDT 1.0")


window.rowconfigure([0, 1, 2, 3], minsize=50, weight=1)
window.columnconfigure([0, 1], minsize=50, weight=1)

lbl_title = tk.Label(master=window, text="UDP File Transfer RDT 1.0")
lbl_title.grid(row=0, column=0, sticky="nsew")

lbl_serverAddress = tk.Label(master=window, text="Server Address (xxx.xxx.x.x:xxxx) : ")
lbl_serverAddress.grid(row=1, column=0, sticky="nsew")

ent_port = tk.Entry(master=window, textvariable=serverAddr)
ent_port.grid(row=1, column=1, sticky="ew")

lbl_output = tk.Label(master=window, text="Output: ")
lbl_output.grid(row=2, column=0, sticky="nsew")

txt_output = tk.Text(master=window)
txt_output.grid(row=2, column=1, sticky="nsew")

btn_open = tk.Button(master=window, text="Open Socket", command=openServer)
btn_open.grid(row=3, column=1, sticky="nsew")

# Calls receive function on startup of tkinter's main function
window.after(0, receive)
window.mainloop()