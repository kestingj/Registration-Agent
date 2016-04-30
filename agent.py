#serviceAddr = ("cse461.cs.washington.edu", 46101) 	

import struct
import socket
import pyuv
import sys
import os
import threading
from threading import Timer
import psutil

class RegistrationAgent(object):

	GLOBAL_PORT = 1266
	NUM_ATTEMPTS = 3

	def __init__(self, hostName, hostPort):
		outSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
		outSocket.bind(("0.0.0.0", self.GLOBAL_PORT))
		outSocket.settimeout(1)
		self.outSocket = outSocket
		inSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
		inSocket.bind(("0.0.0.0", self.GLOBAL_PORT + 1))
		self.inSocket = inSocket
		#self.addr = socket.gethostbyname(socket.gethostname())
		self.addr = "127.0.0.1" #DELETE

		self.serviceAddress = (hostName, hostPort)

		seqNum = -1
		self.seqNum = seqNum

		self.registeredPorts = {}
		
		listening = threading.Thread(target=self.listenForProbe)	
		listening.start()	

	def register(self, port, serviceData, name):
		return self.privateRegister(port, serviceData, name, 0)	

	def privateRegister(self, port, serviceData, name, attempt):
		if attempt == 0: 
			# Only increment on first attempt
			self.incrSeqNum()	
		nameLength = len(name)
	
		
		data = struct.pack(">HBBIHIB{}s".format(nameLength), 50273, self.seqNum, 1, ip2int(self.addr), port, serviceData, nameLength, name)
		
		self.outSocket.sendto(data, self.serviceAddress)
		try:
			receivedData, receivedAddr = self.outSocket.recvfrom(1024)
			lifetime = self.processRegistrationResponse(receivedData)
			if lifetime > 0:
				timer = Timer(lifetime - 1, self.privateRegister, [port, serviceData, name, 0])
				timer.start()
				self.registeredPorts[port] = timer
				#print "Register {}:{} successful: lifetime = {}".format(socket.gethostbyname(socket.gethostname()), self.port, lifetime)
				return lifetime
			else: 	
				return 0

		except socket.timeout:
			print "Timed out waiting for reply to REGISTER message"
			if attempt < self.NUM_ATTEMPTS - 1:
				attempt += 1
				return self.privateRegister(attempt, port, serviceData, attempt)	
			else: 
				print "Sent {} REGISTER messages but got no reply.".format(self.NUM_ATTEMPTS)	
				return 0	

	def fetch(self, prefix):
		return self.privateFetch(prefix, 0)			

	def privateFetch(self, prefix, attempt):
		if attempt == 0:
			self.incrSeqNum()
		prefixLength = len(prefix)
		data = struct.pack(">HBBB{}s".format(prefixLength), 50273, self.seqNum, 3, prefixLength, prefix)
		self.outSocket.sendto(data, self.serviceAddress)
		try:
			receivedData, receivedAddr = self.outSocket.recvfrom(1024)
			responses = self.processFetchData(receivedData)
			return responses		

		except socket.timeout:
			print "Timed out waiting for reply to FETCH message"
			if attempt < self.NUM_ATTEMPTS - 1:
				attempt += 1
				return self.privateFetch(prefix, attempt)	
			else: 
				print "Sent {} FETCH messages but got no reply.".format(self.NUM_ATTEMPTS)
				return None	

	def processFetchData(self, data):
		size = len(data)
		if size > 4:
			# Fetch response
			ver, packetSeqNum, typeNum, numResponses, stringOfResponses = struct.unpack(">HBBB{}s".format(size - 5), data)
			if ver == 50273 and packetSeqNum == self.seqNum and typeNum == 4:
				unpackString = ">"
				for i in range(numResponses):
					unpackString += "10s"
				responses = struct.unpack(unpackString, stringOfResponses)
				decodedResponses = []
				for response in responses:
					decodedResponse = struct.unpack(">IHI", response)
					formattedResponse = [int2ip(decodedResponse[0]), decodedResponse[1], decodedResponse[2]]
					decodedResponses.append(formattedResponse)
				return decodedResponses	
		return None

	def probe(self):
		return self.privateProbe(0)			

	def privateProbe(self, attempt):
		if attempt == 0:
			self.incrSeqNum()
		data = struct.pack(">HBB", 50273, self.seqNum, 6)
		self.outSocket.sendto(data, self.serviceAddress)
		try:
			receivedData, receivedAddr = self.outSocket.recvfrom(1024)
			success = self.processAck(receivedData)
			return success	

		except socket.timeout:
			print "Timed out waiting for reply to PROBE message"
			if attempt < NUM_ATTEMPTS - 1:
				attempt += 1
				return probe(attempt)	
			else: 
				print "Sent {} PROBE messages but got no reply.".format(NUM_ATTEMPTS)
				return False

	def processAck(self, data):
		if len(data) == 4:		
			ver, packetSeqNum, typeNum = struct.unpack(">HBB", data)
			if ver == 50273 and packetSeqNum == self.seqNum and typeNum == 7:	
				return True
		return False

	def unregister(self, port):
		return self.privateUnegister(port, 0)

	def privateUnegister(self, port, attempt):	
		if attempt == 0: 
			# Only increment on first attempt
			self.incrSeqNum()
		
		data = struct.pack(">HBBIH", 50273, self.seqNum, 5, ip2int(self.addr), port) 	
		self.outSocket.sendto(data, self.serviceAddress)
		try:
			receivedData, receivedAddr = self.outSocket.recvfrom(1024)
			
			if port in self.registeredPorts:
				self.registeredPorts[port].cancel()
			return self.processAck(receivedData)	

		except socket.timeout:
			print "Timed out waiting for reply to UNREGISTER message"
			if attempt < self.NUM_ATTEMPTS - 1:
				attempt += 1
				return self.privateUnregister(port, attempt)	
			else: 
				print "Sent {} UNREGISTER messages but got no reply.".format(self.NUM_ATTEMPTS)
				if port in self.registeredPorts:
					self.registeredPorts[port].cancel()
				return False										

	def listenForProbe(self):
		receivedData, receivedAddr = self.inSocket.recvfrom(1024)
		if len(receivedData) == 4:
			verNum, packetSeqNum, typeNum = struct.unpack("HBB", receivedData)
			if verNum == 50273 and typeNum == 6:
				print "I've been probed!"
				ack = struct.pack("HBB", 50273, packetSeqNum, 7)
				self.inSocket.send(receivedAddr, ack)
		listening = threading.Thread(target=self.listenForProbe)	
		listening.start()	

	def processRegistrationResponse(self, data):	
		size = len(data)
		if size == 6:
			# Response to REGISTER
			ver, packetSeqNum, typeNum, lifetime = struct.unpack(">HBBH", data)
			if ver == 50273 and packetSeqNum == self.seqNum and typeNum == 2:	
				return lifetime
			else: 
				return 0			
	
	def incrSeqNum(self):
		self.seqNum += 1
		if self.seqNum > 255:
			self.seqNum = 0

	def close(self):
		for port in self.registeredPorts.keys():
			self.registeredPorts[port].cancel()	
			self.unregister(port)	
			del self.registeredPorts[port]
		self.outSocket.close()
		self.inSocket.close()	

def ip2int(addr):  
	num = struct.unpack("!I", socket.inet_aton(addr))[0]
	return num

def int2ip(addr):                                                               
    return socket.inet_ntoa(struct.pack("!I", addr))	