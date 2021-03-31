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

INTEGRITYCHECK = True

NOERRORSIM = 0
ACKERRORSIM = 1

ERRORSIM = NOERRORSIM


ACKERROR = 10
ERRORCLEARED = False

# Global Variables
filename = ''
file = b''
filePacketsReceived = 0
socket_opened = False
serverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sequenceID = True
activeTransmission = False
dataErrors = 0

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
    txt_output.see("end")


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

            screenPrint(f'--Received Packet SID: {sequenceID} | PID: {packet.ID}--')

            processPacket(packet, clientAddr)


    # This function calls itself every 100ms to allow tkinter's main function to run
    window.after(100, receive)

def initializeLink(clientAddr):
    global sequenceID, ACK, filename, file, activeTransmission, filePacketsReceived, dataErrors
    sequenceID = True
    dataErrors = 0
    ACK = secrets.token_hex(16).encode()
    activeTransmission = True
    screenPrint("--Begin Transmission--")
    screenPrint(f"--ACK: {ACK}--")
    sendACK(clientAddr)
    file = b''
    filename = ""
    filePacketsReceived = 0



def terminateLink(clientAddr):
    global activeTransmission
    screenPrint("--End Transmission--")
    activeTransmission = False
    sendACK(clientAddr)
    writeFile()

def sendNACK(clientAddr):
    nackPacket = Packet.Packet(b'\x00\x00\x00\x00')
    nackPacket.ID = sequenceID
    serverSocket.sendto(pickle.dumps(nackPacket), clientAddr)

def sendACK(clientAddr):
    global ERRORCLEARED
    ackPacket = Packet.Packet(ACK)
    ackPacket.ID = sequenceID
    serverSocket.sendto(pickle.dumps(ackPacket), clientAddr)

def sendERRORACK(clientAddr):
    global ERRORCLEARED
    errorACK = secrets.token_hex(16).encode()
    errAckPacket = Packet.Packet(ACK)
    errAckPacket.data = errorACK
    errAckPacket.ID = sequenceID
    serverSocket.sendto(pickle.dumps(errAckPacket), clientAddr)
    screenPrint("--Sent Bad ACK--")


def processPacket(packet, clientAddr):
    global file, filename, sequenceID, filePacketsReceived, ERRORCLEARED, dataErrors

    checksum = packet.checksum
    packet.generateChecksum()

    if packet.checksum != checksum or sequenceID == packet.ID:
        screenPrint("-- Packet Error --")
        screenPrint(f"--CCS: {checksum} | PCS: {packet.checksum} | SQ: {sequenceID} | PID: {packet.ID}--")
        dataErrors += 1
        if packet.checksum == checksum:
            sequenceID = not packet.ID
            sendACK(clientAddr)
            sequenceID = packet.ID
        else:
            sequenceID = packet.ID
            sendACK(clientAddr)
            sequenceID = not packet.ID

    else:
        if packet.data == SYN_ACK:
            initializeLink(clientAddr)
        elif packet.data == END_TRANSMISSION:
            terminateLink(clientAddr)
            screenPrint(f"--Number of Data Errors: {dataErrors}--")
        elif filename == "":
            filename = packet.data.decode()
            screenPrint(f"--Filename: {filename}--")
            sendACK(clientAddr)
        else:
            screenPrint(f"--Loading File - Packet [{filePacketsReceived}]--")
            file = file + packet.data

            if ERRORSIM == ACKERRORSIM and ((filePacketsReceived % 20) < (ACKERROR/5)) and ERRORCLEARED:
                sendERRORACK(clientAddr)
                dataErrors += 1
                ERRORCLEARED = False
            else:
                screenPrint("--Packet Loaded--")
                sendACK(clientAddr)
                if ERRORSIM != 0:
                    ERRORCLEARED = True
            filePacketsReceived += 1

        sequenceID = packet.ID
    screenPrint("\n")
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