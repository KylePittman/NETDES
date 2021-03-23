import tkinter as tk
import tkinter.filedialog as fd
import socket
import Packet as pkt
import pickle

# Global Constants
BEGIN_TRANSMISSION = 0
END_TRANSMISSION = 1
PACKETSIZE = 1024
INTEGRITYCHECK = True


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
def send():
    global filename

    # Ensure that a file has been selected, and the IPs have been input
    if filename.get() == '':
        screenPrint("--Please Select A File--")
        return

    if clientAddr.get() == '' or serverAddr.get() == '':
        screenPrint("--Please Enter Both Addresses--")
        return

    # Read the file as binary into an array of packets

    try:
        file = open(filename.get(), 'rb')
    except IOError:
        screenPrint("--ERROR OPENING FILE--")
        return

    packets = []

    packetData = file.read(PACKETSIZE)
    sequenceNumber = 0
    while packetData:
        packets.append(pkt.Packet(sequenceNumber, packetData))
        packetData = file.read(PACKETSIZE)
        sequenceNumber += 1


    # Begin transmitting file
    screenPrint("--Sending---")
    psa = parseAddressField(serverAddr)

    # Send notification to server that a file is going to be transmitted
    beginPkt = pkt.Packet(-1,bytes([BEGIN_TRANSMISSION]))
    clientSocket.sendto(pickle.dumps(beginPkt), (psa.IP, psa.port))

    # Parse the name of the file from the path and transmit it to the server
    names = filename.get().split('/')
    namePkt = pkt.Packet(-2,bytes(names[len(names)-1].encode()))
    clientSocket.sendto(pickle.dumps(namePkt), (psa.IP, psa.port))

    # Transmit each packet from the array to the server
    for packet in packets:
        clientSocket.sendto(pickle.dumps(packet), (psa.IP, psa.port))

        # This will receive the packet sent back from the server and check if it is exactly the same as the original
        if INTEGRITYCHECK:
            data, _ = clientSocket.recvfrom(PACKETSIZE)

            integrityCheck = pickle.loads(data)

            if packet == integrityCheck:
                screenPrint("--Transmitted Packet Without Loss--")
            else:
                screenPrint("--Transmitted Packet Failed Integrity Check--")
        else:
            screenPrint(f"--Transmitted Packet {packet.ID}--")

    # Notify the server that all data has been transmitted
    endPkt = pkt.Packet(-3, bytes([END_TRANSMISSION]))
    clientSocket.sendto(pickle.dumps(endPkt), (psa.IP, psa.port))
    screenPrint("--File Transmitted--")

# Open window to select a file
def fileSelect():
    global filename
    filename.set(fd.askopenfile(mode = 'rb').name)

# Print text to window
def screenPrint(msg):
    txt_output.insert(tk.END, f"{msg} \n")


# Window Setup
window = tk.Tk()
clientAddr = tk.StringVar()
serverAddr = tk.StringVar()
filename = tk.StringVar()

window.title("Client RDT 1.0")

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

btn_send = tk.Button(master = window, text = "Send", command = send)
btn_send.grid(row = 5, column = 1, sticky = "nsew")

window.mainloop()