import tkinter as tk
import tkinter.filedialog as fd
import socket
import Packet
import pickle


# Global Constants
BEGIN_TRANSMISSION = 0
END_TRANSMISSION = 1
PACKETSIZE = 1028
RECEIVESIZE = 2048
INTEGRITYCHECK = True

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
    global filename, file

    if socket_opened:
        # wait to recieve a message
        try:
            data, clientAddr = serverSocket.recvfrom(RECEIVESIZE)
        except:
            data = None

        if data is not None:
            pkt = pickle.loads(data)
            screenPrint(f'--Received Packet [{pkt.ID}]--')
            # print received message, and the IP it came from
            if pkt.data == bytes([0]):
                screenPrint("--Begin Transmission--")
                file = b''
            elif pkt.data == bytes([1]):
                screenPrint("--End Transmission--")
                writeFile()
            elif pkt.ID == -2:
                filename = pkt.data.decode()
                screenPrint(f"--Filename: {filename}--")
            else:
                screenPrint("--Loading File--")
                file = file + pkt.data
                # send data back to client for quality check
                if INTEGRITYCHECK:
                    serverSocket.sendto(pickle.dumps(pkt), clientAddr)


    # This function calls itself every 100ms to allow tkinter's main function to run
    window.after(100, receive)


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