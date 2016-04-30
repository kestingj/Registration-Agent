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
		elif command == "u":
			if len(params) != 2:
				print "Incorrect number of arguments"
			else:	
				port = int(params[1])
				agent.unregister(port)		
		elif command == "f":
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
		elif command == "p":
			if len(params) != 1:
				print "Incorrect number of arguments"
			else:	
				success = agent.probe()
				if success:
					print "Success"
				else:
					print "Failure"	
		elif command == "q":
			if len(params) != 1:
				print "Incorrect number of arguments"
			else:
				agent.close()
				os._exit(1)

		else:
			print "Unrecognized command"




if __name__ == "__main__":
	main()