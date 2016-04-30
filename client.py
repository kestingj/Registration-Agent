from agent import RegistrationAgent
import sys
import socket
import os


def main():
	argv = sys.argv

	if len(argv) != 3:
		sys.exit()

	addr = socket.gethostbyname(argv[1])	
	agent = RegistrationAgent(addr, int(argv[2]))

	while True:
		userInput = raw_input("Enter r(egister), u(nregister), f(etch), p(robe), or q(uit): ")
		readStdIn(userInput, agent)	

def readStdIn(data, agent):
	if data is not None and data.strip() is not "":
		params = data.split()
		command = params[0]
		if command == "r":
			register(params, agent)	
		elif command == "u":
			unregister(params, agent)		
		elif command == "f":
			fetch(params, agent)		
		elif command == "p":
			probe(agent)	
		elif command == "q":
			quit(agent)
		else:
			print "Unrecognized command"

def register(params, agent):
	if len(params) != 4:
		print "Incorrect number of arguments"
	else:
		port = int(params[1])
		servData = int(params[2])
		name = params[3]
		if port >= 0 and port < 65535:
			lifetime = agent.register(port, servData, name)
			if lifetime > 0:
				localAddr = socket.gethostbyname(socket.gethostname())
				localAddr = "127.0.0.1" #DELETE	
				print "Register {}:{} successful: lifetime = {}".format(localAddr, port, lifetime)
			else:
				print "Registration failed"	
		else: 
			print "Port must be 0-65534."

def fetch(params, agent):
	responses = None
	if len(params) > 2:
		print "Incorrect number of arguments"
	elif len(params) == 2:
		responses = agent.fetch(params[1])
	else:
		responses = agent.fetch("")	
	if responses is not None:
		for i in range(len(responses)):
			response = responses[i]
			ip, port, serviceData = response
			print "[{}] {} {} {}".format(i, ip, port, serviceData)
	else: 
		print "No entries were fetched"	

def unregister(params, agent):
	if len(params) != 2:
		print "Incorrect number of arguments"
	else:	
		port = int(params[1])
		agent.unregister(port)	

def probe(agent):
	success = agent.probe()
	if success:
		print "Success"
	else:
		print "Failure"

def quit(agent):
	agent.close()
	os._exit(1)	

if __name__ == "__main__":
	main()