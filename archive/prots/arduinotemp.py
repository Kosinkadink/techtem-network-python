#!/usr/bin/python2
import os,sys,socket,select,threading
from time import strftime, sleep

variables = ['gamemode']
servercommands = ["/pm", "/peoplecount"]
standalone = False
version = '2.0test003'
clientfunction = 'tictac_client'
serverfunction = None
running = True

def date():
 	return strftime(".%Y-%m-%d")

def tictac_client_winput(inp_host,inp_port):
	inputsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	inputsock.connect((inp_host,inp_port))

	global running
	while running:
		try:
			userinp = sys.stdin.readline().replace("\n", "")
			if userinp in ('/exit','/quit','/leave'):
				running = False
			inputsock.sendall(userinp)
		except:
			pass

def tictac_client(s,data,location):
	global running
	s.sendall(data[0])
	understand = s.recv(2)
	if understand != 'ok':
		return 'game mode not understood'

	print 'starting tic tac client'


	if os.name == 'nt':
		userinput = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		inp_host = 'localhost'
		inp_port = 9099
		userinput.bind((inp_host,inp_port))
		userinput.listen(1)

		userthread = threading.Thread(target=tictac_client_winput,args=(inp_host,inp_port))
		userthread.daemon = True
		userthread.start()

		user,useless = userinput.accept()

		socket_list = [user, s]

	else:
		socket_list = [sys.stdin, s]

	while 1:
		sleep(.1)
		 
		# Get the list sockets which are readable
		ready_to_read,ready_to_write,in_error = select.select(socket_list , [], [])

		for sock in ready_to_read:
			if sock == s:
				# incoming message from remote server, s
				#try:
				data = sock.recv(4096)
				#except:
				#	print '\nDisconnected from tictac server, could not receive data'
				#	running = False
				#	return 'Returning to Network Client'

				if data:
					if data == 'ready?':
						sock.sendall('ready!')
					elif data.startswith('b||'):
						clear()
						displayBoard(data[3:])
						sock.sendall('b||ok')
					elif data.startswith('e||'):
						print(data[3:])
					elif data.startswith('w||'):
						print(data[3:])
						sock.sendall('w||ok')
						return 'Returning to Network Client'
					elif data.startswith('x||'):
						sock.sendall('x||ok')
						print 'An opponent has left'
						return 'Returning to Network Client'
					else:
						print(data)

				else:
					print '\nDisconnected from tictac server, data = empty'
					return 'Returning to Network Client'
					
			else :
				# user entered a message
				if os.name == 'nt':
					message = sock.recv(4096)
				else:
					message = sys.stdin.readline().replace("\n", "")
				if message:
					if message[0] == "/":# and message.split()[0] not in servercommands:
						if message.split()[0] == "/exit" or message.split()[0] == "/quit" or message.split()[0] == "/leave":
							print "Leaving tictac server."

							running = False
							return
					else:
						#format all the data and send it
						s.send("{}".format(message))

def displayBoard(data):
	print data
	print ''

def clear(): #clear screen, typical way
	if os.name == 'nt':
		os.system('cls')
	else:
		os.system('clear')