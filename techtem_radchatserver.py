#!/usr/bin/python2
import sys, socket, select, os, threading, getopt
from datetime import datetime
from time import strftime, sleep
from hashlib import sha1
from random import randint
try:
	from Crypto.Cipher import AES
	from Crypto import Random
	from Crypto.PublicKey import RSA
	from Crypto.Cipher import PKCS1_OAEP
except ImportError:
	print "NOTICE: PyCrypto not found on Python 2.7; try the command 'pip install pycrypto' or find the package online"
	print "Connections will NOT be encrypted"

#initialization of the server
__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__))) #directory from which this script is ran
if os.name == 'nt':
	__location__ = __location__.replace('\\','/')
sys.path.insert(0, os.path.join(__location__,'resources/source/'))

#import common code
import CommonCode
import CommonCode_Server
CommonCode_Server.__location__ =  __location__
#script-specific variables


class RadchatServer(CommonCode_Server.TemplateServer):

	serversocket = None
	targetaddr = None
	socketlist = []
	addrlist = []
	admintrip = None
	maliciouswords = []


	# don't change this
	netPass = None
	key = None
	pubkey = None
	threads = []
	# change this to default values
	version = '3.0.0'
	serverport = 9009
	send_cache = 40960
	send_cache_enc = 40960
	RSA_bitlength = 2048
	shouldEncrypt = True
	shouldEncryptDownload = True
	scriptname = 'radchat'
	function = 'radchat_client'
	name = 'radchat'
	downloadAddrLoc = 'jedkos.com:9011&&protocols/radchat.py'
	#form is ip:port&&location/on/filetransferserver/file.py

	def __init__(self, serve=serverport):
		CommonCode_Server.TemplateServer.__init__(self,serve)

	def init_spec(self):
		### server specific files start ###
		if not os.path.exists(__location__+'/resources/programparts/radchat'): os.makedirs(__location__+'/resources/programparts/radchat')
		if not os.path.exists(__location__+'/resources/programparts/radchat/logs'): os.makedirs(__location__+'/resources/programparts/radchat/logs')
		if not os.path.exists(__location__+'/resources/programparts/radchat/admintrip.txt'):
			with open(__location__+'/resources/programparts/radchat/admintrip.txt', "a") as makeprot:
				pass
		if not os.path.exists(__location__+'/resources/programparts/radchat/maliciouswords.txt'):
			with open(__location__+'/resources/programparts/radchat/maliciouswords.txt', "a") as makeprot:
				pass

		with open(__location__+'/resources/programparts/radchat/admintrip.txt', "r") as admintripfile: self.admintrip = admintripfile.readline().replace("\n", "")

		#read maliciouswords file and append each line to the list of malicious words

		with open(__location__+'/resources/programparts/radchat/maliciouswords.txt', "r") as maliciouswordsfile:
			for line in maliciouswordsfile:
				self.maliciouswords.append(line.replace("\n",""))
		### server specific files end ###

	def searchlogfor(self,timestamp):
		target = None
		with open(__location__+'/resources/programparts/radchat/logs/'+self.date(), "r") as log:
			for line in log:
				if timestamp in line.split()[0]:
					#find the addr associated with that timestamp
					self.targetaddr = line.split()[-1]
					target = self.socketlist[self.addrlist.index(self.targetaddr)]
		return target

	def date(self):
		return datetime.now().strftime("%Y-%m-%d")

	def timestamp(self):
		return "<{}>".format(datetime.now().strftime("%H:%M:%S.%f"))

	def help(self):
		print "\nclear - clears screen"
		print "help - displays this window"
		print "exit - close server"

	def serverterminal(self): #used for server commands
		while 1:
			inp = raw_input("")
			if inp:
				if inp == 'help':
					self.help()
				elif inp == 'exit':
					self.exit()
				elif inp == 'netpass':
					self.get_netPass()
					print self.netPass
				elif inp == 'clear':
					self.clear()

	def servergen(self):
		global version
		print 'radchat server started - version %s on port %s\n' % (version,self.serverport)
		self.get_netPass()
		netPass = self.netPass
		self.serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		host = ''
		port = self.serverport
		self.serversocket.bind((host, port))
		self.serversocket.listen(10)
		display="" 
		# add server socket object to the list of readable connections
		self.socketlist.append(self.serversocket)
		self.addrlist = [host]
		with open(__location__+'/resources/programparts/radchat/logs/'+self.date(), "a") as log:
			log.write("Server has started. {}\n".format(self.timestamp()))

		while 1 and not self.event.is_set():
			sleep(.1)
			# get the list sockets which are ready to be read through select
			# 4th arg, time_out  = 0 : poll and never block
			ready_to_read,ready_to_write,in_error = select.select(self.socketlist,[],[],0)

			for sock in ready_to_read:
				# a new connection request recieved
				if sock == self.serversocket:
					#This is partially a placeholder variable, but also makes sense because the current socet is the server socket
					clientsocket,addr = self.serversocket.accept()
					print("Got a connection from %s" % str(addr))
					try:
						clientsocket.recv(2)
						if netPass != None:
							rightPass = self.netPass_check(clientsocket)
						else:
							rightPass = True
							clientsocket.sendall('np')

						if rightPass == True:
							identity = clientsocket.recv(1024)
							compat = 'n'
							scriptname,function,cli_version = identity.split(':')
							if scriptname == 'radchat' and function == 'chat_client' and cli_version == version:
								compat = 'y'

							clientsocket.sendall(compat)

							if compat != 'y': #not a sync_client, so respond with 
								clientsocket.recv(2)
								clientsocket.sendall('n|radchat:chat_client:%s|%s' % (version,self.downloadprot))
								print 'does not have protocol'
								clientsocket.close
							else:
								print 'HAS protocol'
								clientsocket.recv(2)
								clientsocket.sendall('ok')
								self.socketlist.append(clientsocket)
								addr = addr[0]
								#because the IP and socket are appended to their corresponding lists at the same time, they will share the same index value
								self.addrlist.append(addr)
								#turn the sock ID into a 4-digit string to make it easier to read from the log
								self.broadcast(addr, "{}: Someone has entered the chat. There is currently {} people in the chatroom.".format(self.timestamp(), len(self.socketlist)-1))
					except Exception,e:
						print str(e) + '\n'
					# a message from a client, not a new connection
				else:
					#figure out what the IP is for the sending client
					addr = self.addrlist[self.socketlist.index(sock)]
					# process data recieved from client
					try:
						# receiving data from the socket.
						data = sock.recv(4096)
					except:
						self.broadcast(addr, "{}: Someone has disconnected. There is currently {} people in the chatroom.".format(self.timestamp(), len(self.socketlist)-1))
						continue
					if data:
						message = ""
						name = ""
						tripcode = ""
						pm = False
						target = ""
						command = ""
						malicious = False

						try:
							#message, name, tripcode = data.splitlines()
							message = data.splitlines()[0]
							name = data.splitlines()[1]
						except:
							sock.send("invalid message")
						try:
							tripcode = data.splitlines()[2]
						except:
							pass

						tobesent = self.timestamp()
						if message.split()[0] =="/pm":
							pm = True
							if len(message.split()) > 2:
								target = message.split()[1]
								target = self.searchlogfor(target)
								message = message[len(message.split()[0]) + len(message.split()[1]) + 1:]
								tobesent += " ##pm##"
							else:
								message = ""
						if self.admintrip and tripcode == self.admintrip:
							tobesent += " ##admin##"
						else:
							if not name.replace(" ", ""):
								name = "Anonymous"
							tobesent += " [{}]".format(name)
							if tripcode:
								tobesent+= " {{{}}}".format(sha1(tripcode).hexdigest()[-7:-1])
						if not pm and message[0] == "/":
							command = message.split()[0]
						tobesent += ": {}".format(message)

						for phrase in self.maliciouswords:
							if phrase in message:
								malicious = True

						if command:
							if command == "/peoplecount":
								sock.send("there is currently {} people in the chatroom".format(len(self.socketlist)-1))
							else:
								sock.send("invalid command")
						elif pm:
							if message:
								if target:
									try:
										target.send(tobesent)
										with open(__location__+'/resources/programparts/radchat/logs/'+self.date(), "a") as log: log.write("{} [sent to IP: {}] {}\n".format(tobesent, self.targetaddr, addr))
									except:
										sock.send("that person is disconnected")
								else:
									sock.send("target not found")
							else:
								sock.send("poorly formatted pm")
						elif malicious:
							self.broadcast(addr, "{} {} has said malicious words".format(self.timestamp(), name))
						else:
							self.broadcast(addr, tobesent)
					else:
						# remove the socket that's broken
						if sock in self.socketlist:
							self.addrlist.remove(self.addrlist[self.socketlist.index(sock)])
							self.socketlist.remove(sock)
							# at this stage, no data means probably the connection has been broken
							self.broadcast(addr, "{}: Someone has disconnected. There is currently {} people in the chatroom.".format(self.timestamp(), len(self.socketlist)-1))

		self.serversocket.close()

	# broadcast chat messages to all connected clients
	def broadcast(self, addr, message):
		for socket in self.socketlist:
			# send the message only to peer
			if socket != self.serversocket:
				try :
					socket.send(message)
				except :
					# broken socket connection
					socket.close()
					# broken socket, remove it
					if socket in self.socketlist:
						self.socketlist.remove(socket)
		with open(__location__+'/resources/programparts/radchat/logs/'+self.date(), "a") as log:
			log.write(message + " " + addr + "\n")

	def exit(self): #kill all processeses for a tidy exit
		quit()

if __name__ == '__main__':
	CommonCode_Server.main(sys.argv[1:],TemplateServer)