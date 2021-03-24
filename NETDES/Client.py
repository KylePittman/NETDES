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
PACKETSIZE = 1024
RECIEVESIZE = 2048
INTEGRITYCHECK = True
SEQUENCEID = False
ACK = -1

# Global variables for socket interaction
socket_opened = False
clientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Simple class to store IP and port together
class Address:
    def __init__(self, IP, port):
        self.IP = IP
        self.port = int(port)


# Open socket to send/receive from
def openSocket():
    global socket_opened
    
    if socket_opened:
        return
    address = parseAddressField(clientAddr)
    screenPrint(f"--Opening Socket Port: {address.port}--")
    clientSocket.bind((address.IP, address.port))
    socket_opened = True


# Used to get user input from address fields
def parseAddressField(field):
    temp = field.get().split(":")
    return Address(IP = temp[0], port = temp[1])

# Reads in file and transmits it to server
def sendFile():
    global filename

    # Ensure that a file has been selected, and the IPs have been input
    if filename.get() == '':
        screenPrint("--Please Select A File--")
        return

    if clientAddr.get() == '' or serverAddr.get() == '':
        screenPrint("--Please Enter Both Addresses--")
        return

    fileData = segmentFile()

    # Begin transmitting file
    screenPrint("--Sending---")
    psa = parseAddressField(serverAddr)
    # Send notification to server that a file is going to be transmitted
    synack(psa)

    # Parse the name of the file from the path and transmit it to the server
    transmitFileName(psa)

    # Transmit each packet from the array to the server
    transmitFile(fileData, psa)

    # Notify the server that all data has been transmitted
    terminateStream(psa)


# Open window to select a file
def fileSelect():
    global filename
    filename.set(fd.askopenfile(mode = 'rb').name)

def segmentFile():
    # Read the file as binary into an array of packets

    try:
        file = open(filename.get(), 'rb')
    except IOError:
        screenPrint("--ERROR OPENING FILE--")
        return

    fileData = []

    packetData = file.read(PACKETSIZE)

    while packetData:
        fileData.append(packetData)
        packetData = file.read(PACKETSIZE)

    return fileData

def sendPacket(packet, psa):
    clientSocket.sendto(pickle.dumps(packet), (psa.IP, psa.port))

def receivePacket(prevPacket, psa):
    screenPrint("--Waiting for ACK--")
    try:
        data, _ = clientSocket.recvfrom(RECIEVESIZE)
    except:
        data = None

    if data is not None:
        packet = pickle.loads(data)
        screenPrint(f"--ACK: {packet.data} | PID: {packet.ID}--")
        checksum = packet.checksum
        packet.generateChecksum()

        if packet.checksum != checksum or SEQUENCEID != packet.ID or (ACK != -1 and ACK != packet.data):
            screenPrint("--Resending--")
            sendPacket(prevPacket, psa)
            return receivePacket(prevPacket, psa)
        screenPrint("--Received ACK--")
        return packet
    return receivePacket(prevPacket, psa)



def pack(data):
    global SEQUENCEID
    packet = Packet.Packet(data)
    packet.ID = SEQUENCEID
    SEQUENCEID = not SEQUENCEID
    return packet

def synack(psa):
    global ACK
    synackPacket = pack(SYN_ACK)

    sendPacket(synackPacket, psa)
    ackPacket = receivePacket(synackPacket, psa)
    ACK = ackPacket.data
    screenPrint(f"--ACK: {ACK}--")

def transmitFileName(psa):
    names = filename.get().split('/')
    namePacket = pack(names[len(names) - 1].encode())
    screenPrint("--Transmitting File Name--")
    sendPacket(namePacket, psa)

    receivePacket(namePacket, psa)


def transmitFile(fileData, psa):
    for index, packetData in enumerate(fileData):
        screenPrint(f"--Transmitting Packet [{index}] of [{len(fileData)}]--")
        packet = pack(packetData)
        sendPacket(packet, psa)
        screenPrint("--Transmitted Packet--")

        receivePacket(packet, psa)


def terminateStream(psa):
    screenPrint("--File Sent--")
    eosPacket = pack(END_TRANSMISSION)
    sendPacket(eosPacket, psa)
    receivePacket(eosPacket, psa)


# Print text to window
def screenPrint(msg):
    txt_output.insert(tk.END, f"{msg} \n")


# Window Setup
window = tk.Tk()
clientAddr = tk.StringVar()
serverAddr = tk.StringVar()
filename = tk.StringVar()

window.title("Client RDT 2.2")

window.rowconfigure([0, 1, 2, 3, 4, 5], minsize = 50, weight = 1)
window.columnconfigure([0, 1], minsize = 50, weight = 1)

lbl_title = tk.Label(master = window, text = "UDP File Transfer RDT 1.0")
lbl_title.grid(row = 0, column = 0, sticky = "nsew")


lbl_clientAddress = tk.Label(master = window, text = "Client Address (xxx.xxx.x.x:xxxx) : ")
lbl_clientAddress.grid(row = 1, column = 0, sticky = "nsew")

ent_clientAddress = tk.Entry(master = window, textvariable = clientAddr)
ent_clientAddress.grid(row = 1, column = 1, sticky = "ew")

lbl_serverAddress = tk.Label(master = window, text = "Server Address (xxx.xxx.x.x:xxxx) : ")
lbl_serverAddress.grid(row = 2, column = 0, sticky = "nsew")

ent_port = tk.Entry(master = window, textvariable = serverAddr)
ent_port.grid(row = 2, column = 1, sticky = "ew")

btn_file = tk.Button(master = window, text = "Select File", command = fileSelect)
btn_file.grid(row = 3, column = 0, sticky = "nsew")

ent_file = tk.Entry(master = window, textvariable = filename)
ent_file.grid(row = 3, column = 1, sticky = "ew")

lbl_output = tk.Label(master = window, text = "Output: ")
lbl_output.grid(row = 4, column = 0, sticky = "nsew")

txt_output = tk.Text(master = window)
txt_output.grid(row = 4,column = 1, sticky = "nsew")

btn_open = tk.Button(master = window, text = "Open Socket", command = openSocket)
btn_open.grid(row = 5, column = 0, sticky = "nsew")

btn_send = tk.Button(master = window, text = "Send", command = sendFile)
btn_send.grid(row = 5, column = 1, sticky = "nsew")

window.mainloop()