import tkinter as tk
import tkinter.filedialog as fd
import socket
import Packet
import pickle
import time

# Global Constants
BEGIN_TRANSMISSION = Packet.BEGIN_TRANSMISSION
SYN_ACK = Packet.SYN_ACK
END_TRANSMISSION = Packet.END_TRANSMISSION
PACKETSIZE = 1024
RECIEVESIZE = 2048
INTEGRITYCHECK = True

NOERRORSIM = 0
DATAERRORSIM = 1
PACKETLOSSSIM = 2

ERRORLIST = ("No Errors", "Data Errors", "Data Packet Loss")


ERRORSIM = NOERRORSIM

DATAERROR = 20
ERRORCLEARED = False

ACK = -1

# Global variables
socket_opened = False
clientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sequenceID = False

dataErrors = 0
startTime = 0


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
    global filename, dataErrors
    parseErrorField()
    dataErrors = 0
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
    screenPrint(f"--Number of Data Errors: {dataErrors}--")


# Open window to select a file
def fileSelect():
    global filename
    filename.set(fd.askopenfile(mode = 'rb').name)


# Read in file and split it into an array of datum for transmission
def segmentFile():
    # Read the file as binary into an array of packets

    try:
        file = open(filename.get(), 'rb')
    except IOError:
        screenPrint("--ERROR OPENING FILE--")
        return

    # Initialize fileData to a null array
    fileData = []

    # Read in file
    packetData = file.read(PACKETSIZE)

    # Create Data stream
    while packetData:
        fileData.append(packetData)
        packetData = file.read(PACKETSIZE)

    return fileData


# Function to send packet, and update upload status in window
def sendPacket(packet, psa):
    screenPrint(f"--Sending ID: {packet.ID}--")
    clientSocket.sendto(pickle.dumps(packet), (psa.IP, psa.port))
    window.update()


# Function to corrupt and send data packet
def sendErrorPacket(packet, psa):

    errorPacket = Packet.Packet(b'\x11\x22\x33\x44')
    errorPacket.checksum = packet.checksum
    errorPacket.ID = packet.ID
    screenPrint("--Sending Bad Data--")
    sendPacket(errorPacket, psa)


# Function to handle reception of data from server
def receivePacket(prevPacket, psa):
    global dataErrors, ERRORSIM, ERRORCLEARED
    screenPrint("--Waiting for ACK--")
    try:
        clientSocket.settimeout(.15)
        data, _ = clientSocket.recvfrom(RECIEVESIZE)
    # Timeout exception catch (Resend packet in event of timeout)
    except:
        data = None
        dataErrors += 1
        screenPrint("--Socket Timeout - Resending --")
        sendPacket(prevPacket, psa)

    # Process valid data
    if data is not None:
        packet = pickle.loads(data)
        screenPrint(f"--ACK: {packet.data} | PID: {packet.ID}--")
        checksum = packet.checksum
        packet.generateChecksum()

        # Verify validity of data, resend packet if data is not appropriate
        if packet.checksum != checksum or sequenceID != packet.ID:
            screenPrint(f"--Resending {prevPacket.ID}--")
            sendPacket(prevPacket, psa)
            dataErrors += 1
            return receivePacket(prevPacket, psa)

        # If data is valid, return the packet
        screenPrint("--Received ACK--\n")
        ERRORCLEARED = True
        return packet
    return receivePacket(prevPacket, psa)


# Package data into a packet, increment sequence ID
def pack(data):
    global sequenceID
    packet = Packet.Packet(data)
    packet.ID = sequenceID
    sequenceID = not sequenceID
    return packet


# Begin transmission for a request of ACK
def synack(psa):
    global ACK, sequenceID
    sequenceID = False
    screenPrint(f'--SYNACK ID: {sequenceID}')
    synackPacket = pack(SYN_ACK)

    sendPacket(synackPacket, psa)
    ackPacket = receivePacket(synackPacket, psa)
    ACK = ackPacket.data
    screenPrint(f"--ACK: {ACK}--")
    startTimer()


# Transmit the name of the file
def transmitFileName(psa):
    names = filename.get().split('/')
    namePacket = pack(names[len(names) - 1].encode())
    screenPrint("--Transmitting File Name--")
    sendPacket(namePacket, psa)

    receivePacket(namePacket, psa)


# Transmit the file
def transmitFile(fileData, psa):
    global ERRORCLEARED, dataErrors
    for index, packetData in enumerate(fileData):
        screenPrint(f"--Transmitting Packet [{index}] of [{len(fileData) - 1}]--")
        packet = pack(packetData)

        # Corrupt DATAERROR % of packets
        if ERRORSIM == DATAERRORSIM and ((index % 20) < (DATAERROR / 5)) and ERRORCLEARED:
            screenPrint("--Enter Bad Packet--")
            sendErrorPacket(packet, psa)
            ERRORCLEARED = False

        # Drop DATAERROR % of packets
        elif ERRORSIM == PACKETLOSSSIM and ((index % 20) < (DATAERROR / 5)) and ERRORCLEARED:
            screenPrint("--Dropped Packet--")
            ERRORCLEARED = False

        # Default path, send proper ACK
        else:
            sendPacket(packet, psa)
            screenPrint("--Transmitted Packet--")
            ERRORCLEARED = True

        # Wait for ACK
        receivePacket(packet, psa)


# Send EOS packet to terminate transmission
def terminateStream(psa):
    screenPrint("--File Sent--")
    eosPacket = pack(END_TRANSMISSION)
    sendPacket(eosPacket, psa)
    receivePacket(eosPacket, psa)
    transmissionTime = time.perf_counter() - startTime
    screenPrint(f"--Transmission Time: {transmissionTime} seconds--")


# Print text to window
def screenPrint(msg):
    txt_output.insert(tk.END, f"{msg} \n")
    txt_output.see("end")


# Determine which error simulation will be utilized
def parseErrorField():
    global ERRORSIM
    print(ERRORSELECT.get())
    if ERRORSELECT.get() == ERRORLIST[NOERRORSIM]:
        ERRORSIM = NOERRORSIM
    elif ERRORSELECT.get() == ERRORLIST[DATAERRORSIM]:
        ERRORSIM = DATAERRORSIM
    else:
        ERRORSIM = PACKETLOSSSIM

def startTimer():
    global startTime
    startTime = time.perf_counter()


# Only runs window setup once
if __name__ == "__main__":

    # Window Setup
    window = tk.Tk()
    clientAddr = tk.StringVar()
    serverAddr = tk.StringVar()
    filename = tk.StringVar()

    window.title("Client RDT 3.0")

    window.rowconfigure([0, 1, 2, 3, 4, 5], minsize = 50, weight = 1)
    window.columnconfigure([0, 1], minsize = 50, weight = 1)

    lbl_title = tk.Label(master = window, text = "Error Simulation Type: ")
    lbl_title.grid(row = 0, column = 0, sticky = "nsew")

    ERRORSELECT = tk.StringVar(window)
    ERRORSELECT.set(ERRORLIST[0])
    om_ErrorSelection = tk.OptionMenu(window, ERRORSELECT, *ERRORLIST)
    om_ErrorSelection.grid(row = 0, column = 1, sticky = "nsew")

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
    txt_output.see(tk.END)

    btn_open = tk.Button(master = window, text = "Open Socket", command = openSocket)
    btn_open.grid(row = 5, column = 0, sticky = "nsew")

    btn_send = tk.Button(master = window, text = "Send", command = sendFile)
    btn_send.grid(row = 5, column = 1, sticky = "nsew")

    window.mainloop()