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






















def tictac_client_windows(s,data,location):

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
	while 1:
		 
		# Get the list sockets which are readable
		ready_to_read,ready_to_write,in_error = select.select(socket_list , [], [])

		for sock in ready_to_read:			 
			if sock == s:
				# incoming message from remote server, s
				data = sock.recv(4096)
				if not data :
					print '\nDisconnected from chat server'
					return
				else :
					sys.stdout.write(data) #prints the entire log. alll of it.
					#sys.stdout.write('\n\n{}'.format(data)) # skips to new first line, rewrites name.
					sys.stdout.flush()
					
			else :
				# user entered a message
				message = sock.recv(4096)
				if message:
					if message[0] == "/" and message.split()[0] not in servercommands:
						if message.split()[0] == "/exit" or message.split()[0] == "/quit" or message.split()[0] == "/leave":
							print "Leaving chat server."
							global running
							running = False
							return "Left chat server, back in main client"
					else:
						#format all the data and send it
						s.send("{}".format(message))
				sys.stdout.write('[{}] '.format('waiting for server input'))
				sys.stdout.flush()

def tictac_clientold(inputsocket,data,location):

	if os.name == 'nt':
		return chat_client_windows(inputsocket,data,location)

	#initialize radchat client files
	if not os.path.exists(location+'/resources/programparts/radchat'): os.makedirs(location+'/resources/programparts/radchat')
	if not os.path.exists(location+'/resources/programparts/radchat/logs'): os.makedirs(location+'/resources/programparts/radchat/logs')
	if not os.path.exists(location+'/resources/programparts/radchat/settings.txt'):
		with open(location+'/resources/programparts/radchat/settings.txt', "a") as settingsfile:
			settingsfile.write("")

	#introduce variables
	name = data[0]
	tripcode = data[1]

	#if there is a settings file, read it
	if os.path.isfile(location + '/resources/programparts/radchat/settings.txt'):
		with open(location + '/resources/programparts/radchat/settings.txt') as settingsfile:
			for line in settingsfile:
				if line.split()[0] == "name":
					name = line[5:].replace("\n","")
				if line.split()[0] == "tripcode":
					tripcode = line[9:].replace("\n", "")
				if line.split()[0] == "host":
					host = line[5:].replace("\n","")
				if line.split()[0] == "port":
					port = int(line[5:].replace("\n",""))

	s = inputsocket

	sys.stdout.write("\n[{}] ".format(name)); sys.stdout.flush()

	while 1:
		socket_list = [sys.stdin, s]
		 
		# Get the list sockets which are readable
		ready_to_read,ready_to_write,in_error = select.select(socket_list , [], [])
		 
		for sock in ready_to_read:			 
			if sock == s:
				# incoming message from remote server, s
				data = sock.recv(4096)
				if not data :
					print '\nDisconnected from chat server'
					return
				else :
					with open(location+'/resources/programparts/radchat/logs/client'+date(), "a") as log:
						log.write(data + "\n")
					os.system('cls' if os.name == 'nt' else 'tput reset') #cross platform screen clearing. this just in, clears the ENTIRE SHELL
					with open(location+'/resources/programparts/radchat/logs/client'+date(), "r") as log:
						sys.stdout.write(log.read()) #prints the entire log. alll of it.
					sys.stdout.write('\n\n[{}] '.format(name)) # skips to new first line, rewrites name.
					sys.stdout.flush()
					
			else :
				# user entered a message
				message = sys.stdin.readline().replace("\n", "")
				if message:
					if message[0] == "/" and message.split()[0] not in servercommands:
						#that message was a command
						if message.split()[0] == "/changename": 
							name = message[len(message.split()[0])+1:].replace("\n","")
							if not name:
								name = "Anonymous"
						elif message.split()[0] == "/changetripcode":
							tripcode = message[len(message.split()[0])+1:].replace("\n","")
						elif message.split()[0] == "/exit" or message.split()[0] == "/quit" or message.split()[0] == "/leave":
							print "Leaving chat server."
							return
						elif message.split()[0] == "/help" or message.split()[0] == "/?":
							sys.stdout.write("\nThanks for using the radchat client. Here are the commands you currently have available:\n/changename + new name: changes your name\n/changetripcode + new tripcode: changes your trip code.\n/quit OR /leave: exits gracefully\n/help OR /?: Displays this menu.\n")
						else:
							print "Invalid command"
					else:
						#format all the data and send it
						s.send("{}\n{}\n{}".format(message, name, tripcode))
				sys.stdout.write('[{}] '.format(name))
				sys.stdout.flush()

def chat_client_windows(inputsocket,data,location):
	#initialize radchat client files
	if not os.path.exists(location+'/resources/programparts/radchat'): os.makedirs(location+'/resources/programparts/radchat')
	if not os.path.exists(location+'/resources/programparts/radchat/logs'): os.makedirs(location+'/resources/programparts/radchat/logs')
	if not os.path.exists(location+'/resources/programparts/radchat/settings.txt'):
		with open(location+'/resources/programparts/radchat/settings.txt', "a") as settingsfile:
			settingsfile.write("")

	#introduce variables
	name = data[0]
	tripcode = data[1]

	#if there is a settings file, read it
	if os.path.isfile(location + '/resources/programparts/radchat/settings.txt'):
		with open(location + '/resources/programparts/radchat/settings.txt') as settingsfile:
			for line in settingsfile:
				if line.split()[0] == "name":
					name = line[5:].replace("\n","")
				if line.split()[0] == "tripcode":
					tripcode = line[9:].replace("\n", "")
				if line.split()[0] == "host":
					host = line[5:].replace("\n","")
				if line.split()[0] == "port":
					port = int(line[5:].replace("\n",""))

	s = inputsocket

	sys.stdout.write("\n[{}] ".format(name)); sys.stdout.flush()

	userinput = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	inp_host = 'localhost'
	inp_port = 9099
	userinput.bind((inp_host,inp_port))
	userinput.listen(1)

	userthread = threading.Thread(target=chat_client_winput,args=(inp_host,inp_port))
	userthread.daemon = True
	userthread.start()

	user,useless = userinput.accept()

	while 1:
		socket_list = [user, s]
		 
		# Get the list sockets which are readable
		ready_to_read,ready_to_write,in_error = select.select(socket_list , [], [])
		 
		for sock in ready_to_read:			 
			if sock == s:
				# incoming message from remote server, s
				data = sock.recv(4096)
				if not data :
					print '\nDisconnected from chat server'
					return
				else :
					with open(location+'/resources/programparts/radchat/logs/client'+date(), "a") as log:
						log.write(data + "\n")
					os.system('cls' if os.name == 'nt' else 'tput reset') #cross platform screen clearing. this just in, clears the ENTIRE SHELL
					with open(location+'/resources/programparts/radchat/logs/client'+date(), "r") as log:
						sys.stdout.write(log.read()) #prints the entire log. alll of it.
					sys.stdout.write('\n\n[{}] '.format(name)) # skips to new first line, rewrites name.
					sys.stdout.flush()
					
			else :
				# user entered a message
				message = sock.recv(4096)
				if message:
					if message[0] == "/" and message.split()[0] not in servercommands:
						#that message was a command
						if message.split()[0] == "/changename": 
							name = message[len(message.split()[0])+1:].replace("\n","")
							if not name:
								name = "Anonymous"
						elif message.split()[0] == "/changetripcode":
							tripcode = message[len(message.split()[0])+1:].replace("\n","")
						elif message.split()[0] == "/exit" or message.split()[0] == "/quit" or message.split()[0] == "/leave":
							print "Leaving chat server."
							global running
							running = False
							return "Left chat server, back in main client"
						elif message.split()[0] == "/help" or message.split()[0] == "/?":
							sys.stdout.write("\nThanks for using the radchat client. Here are the commands you currently have available:\n/changename + new name: changes your name\n/changetripcode + new tripcode: changes your trip code.\n/quit OR /leave: exits gracefully\n/help OR /?: Displays this menu.\n")
						else:
							print "Invalid command"
					else:
						#format all the data and send it
						s.send("{}\n{}\n{}".format(message, name, tripcode))
				sys.stdout.write('[{}] '.format(name))
				sys.stdout.flush()