import struct
import socket

def main():
	privateProbe()

def privateProbe():
	outSocket = outSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
	outSocket.bind(("0.0.0.0", 12345))
	data = struct.pack(">HBB", 50273, 1, 6)
	outSocket.sendto(data, ("127.0.0.1", 1275))
	
	receivedData, receivedAddr = outSocket.recvfrom(1024)
	processAck(receivedData)
		
def processAck(data):
	if len(data) == 4:		
		ver, packetSeqNum, typeNum = struct.unpack(">HBB", data)
		if ver == 50273 and packetSeqNum == 1 and typeNum == 7:	
			print "YEP"
	print "NOPE"

if __name__ == "__main__":
	main()			