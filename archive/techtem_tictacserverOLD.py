#!/usr/bin/python2
import sys, socket, select, os, threading, subprocess, getopt
from time import strftime, sleep, time
from hashlib import sha1
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
version = '2.0test003'
#script-specific variables

class TicTacServer(threading.Thread):

	netPass = None
	threads = []
	serverport = 9020
	socketlist2d = []
	socketlist3d = []
	addrlist2d = []
	addrlist3d = []
	downloadprot = ''
	send_cache = 40960
	send_cache_enc = 40960
	RSA_bitlength = 2048
	AES_keysize = 32 #16, 24, 32 
	key = None
	pubkey = None
	shouldEncrypt = False

	def __init__(self, serve=serverport):
		threading.Thread.__init__(self)
		self.event = threading.Event()
		self.serverport = int(serve)

	def run(self):
		self.initialize()

	def run_processes(self):
		serverprocess = threading.Thread(target=self.servergen)
		self.threads.append(serverprocess)
		serverprocess.daemon = True
		serverprocess.start() #starts server process in another thread

		tictac2dprocess = threading.Thread(target=self.tictac2dthread)
		self.threads.append(tictac2dprocess)
		tictac2dprocess.daemon = True
		tictac2dprocess.start() #starts tictac2d thread

		tictac3dprocess = threading.Thread(target=self.tictac3dthread)
		self.threads.append(tictac3dprocess)
		tictac3dprocess.daemon = True
		tictac3dprocess.start() #starts tictac3d thread

		self.serverterminal() #starts command input

	def initialize(self):
		if not os.path.exists(__location__+'/resources'): os.makedirs(__location__+'/resources')
		if not os.path.exists(__location__+'/resources/protocols'): os.makedirs(__location__+'/resources/protocols') #for protocol scripts
		if not os.path.exists(__location__+'/resources/cache'): os.makedirs(__location__+'/resources/cache') #used to store info for protocols and client
		if not os.path.exists(__location__+'/resources/programparts'): os.makedirs(__location__+'/resources/programparts') #for storing protocol files
		if not os.path.exists(__location__+'/resources/uploads'): os.makedirs(__location__+'/resources/uploads') #used to store files for upload
		if not os.path.exists(__location__+'/resources/downloads'): os.makedirs(__location__+'/resources/downloads') #used to store downloaded files
		if not os.path.exists(__location__+'/resources/networkpass'): os.makedirs(__location__+'/resources/networkpass') #contains network passwords
		self.gen_protlist()
		self.init_spec()
		self.get_netPass()
		self.run_processes()

	def init_spec(self):
		### server specific files start ###
		### server specific files end ###
		self.gen_RSA_key()

	def gen_RSA_key(self):
		try:
			print "Generating RSA key (%s bit)..." % self.RSA_bitlength
			self.key = RSA.generate(self.RSA_bitlength)
			print "Done generating RSA key!"
			self.pubkey = self.key.publickey()
		except NameError:
			self.shouldEncrypt = False
		else:
			self.shouldEncrypt = True

	def gen_protlist(self):
		if os.path.exists(__location__+'/resources/protocols/protlist.txt'):
			os.remove(__location__+'/resources/protocols/protlist.txt')
		if not os.path.exists(__location__+'/resources/protocols/protlist.txt'):
			with open(__location__+'/resources/protocols/protlist.txt', "a") as protlist: #file used for identifying what protocols are available
				pass

		addedprots = [] #list for protocols already in protlist.txt
		folderprots = [] #list of all protocols in folder
		with open(__location__+'/resources/protocols/protlist.txt', "r+") as protlist:
			for line in protlist:
				if line.endswith('\n'):
					addedprots += [line[:-1]]
				else:
					addedprots += [line]
			for file in os.listdir(__location__+'/resources/protocols/'):
				if file.endswith('.py'):
					folderprots += [file.split('.py')[0]]
			for item in folderprots: #add any protocols to protlist.txt that are in folder but not already in file
				if item not in addedprots:
					protlist.write(item + '\n')

		#with a working protlist.txt, the protocol scripts are now imported
		with open(__location__+'/resources/protocols/protlist.txt') as protlist:
			for line in protlist:
				try:
					prot = line.split('\n')[0]
				except:
					prot = line
				if line != '':
					filename = __location__ + '/resources/protocols/' + prot + '.py'
					directory, module_name = os.path.split(filename)
					module_name = os.path.splitext(module_name)[0]

					path = list(sys.path)
					sys.path.insert(0,directory)
					try:
						module = __import__(module_name) #cool import command
					finally:
						sys.path[:] = path

	def get_netPass(self):
		if not os.path.exists(__location__+'/resources/networkpass/default.txt'):
			with open(__location__+'/resources/networkpass/default.txt', "a") as protlist: #file used for identifying what protocols are available
				pass
			self.netPass = None
		else:
			with open(__location__+'/resources/networkpass/default.txt', "r") as protlist: #file used for identifying what protocols are available
				netpassword = protlist.readline()
			if netpassword != '':
				self.netPass = netpassword
			else:
				self.netPass = None

	def serverterminal(self): #used for server commands
		while 1:
			inp = raw_input("")
			if inp:
				if inp == 'exit':
					quit()

	def tictac2d(self,socklist,addrlist):
		prop = ['0','1','2','3','4','5','6','7','8']
		mark = ['X','O']
		b = [' ']*9
		turn = 0

		newboard,win,winner = self.gameboard2d(b)

		print 'two users in a match'
		for sock in socklist:
			try:
				sock.sendall('b||' + newboard)
				sock.recv(5)
			except:
				print 'a player has left'
				return

		while 1:
			sleep(.1)
			
			ready_to_read,ready_to_write,in_error = select.select(socklist,[],[],0)
			for sock in ready_to_read:
				addr = addrlist[socklist.index(sock)]
				playerReq = socklist.index(sock)

				try:
					data = sock.recv(1024)
				except:
					print 'a bad playa disconnected, game disbanded $%$%$'
					return
				if data:
					if playerReq == turn % 2:
						if data.startswith('/exit'):
							for sock2 in socklist:
								if sock != sock2:
									try:
										sock2.sendall('player %s has left the match, game disbanded' % mark[playerReq])
										return
									except:
										print 'both players have left, game disbanded'
										return
						else:
							if data in prop:
								if b[int(data)] == ' ':
									b[int(data)] = mark[turn % 2]
								else:
									sock.sendall('e||Position already full. Choose a different position.')
									continue
							else:
								sock.sendall('e||Not a valid position')
								continue
						#sock.sendall('message received')
						newboard,win,winner = self.gameboard2d(b)
						for sock2 in socklist:
							try:
								sock2.sendall('b||' + newboard)
								sock2.recv(5)
							except:
								print 'a poor player has left, game disbanded'
								return
						if win:
							for sock2 in socklist:
								try:
									sock2.sendall('w||%s has won!' % winner)
									sock.recv(5)
								except:
									print 'a sour loser has left, still counts ;)'
									return
							print "game is over!"
							return
						turn += 1
						if turn >= 9:
							for sock2 in socklist:
								try:
									sock2.sendall('w||Tie!')
									sock2.recv(5)
								except:
									print 'a player has left, still a tie though'
									return
							print "game is over!"
							return
					else:
						sock.sendall('e||It is not your turn')
						continue
				else:
					print 'a player has left'
					for sock2 in socklist:
						try:
							sock2.sendall('x||')
							sock2.recv(5)
						except:
							pass
					return




	def gameboard2d(self,b):
		board = ''
		lines = []
		lines += ["  - - - - - -"]
		lines += [" | %s | %s | %s |" % (0,1,2)]
		lines += ["  - - - - - -"]
		lines += [" | %s | %s | %s |" % (3,4,5)]
		lines += ["  - - - - - -"]
		lines += [" | %s | %s | %s |" % (6,7,8)]
		lines += ["  - - - - - -"] 
		lines += ['']
		lines += ["  - - - - - -"]
		lines += [" | %s | %s | %s |" % (b[0],b[1],b[2])]
		lines += ["  - - - - - -"]
		lines += [" | %s | %s | %s |" % (b[3],b[4],b[5])]
		lines += ["  - - - - - -"]
		lines += [" | %s | %s | %s |" % (b[6],b[7],b[8])]
		lines += ["  - - - - - -"] 
		for line in lines:
			board += line + '\n'
			win,winner = self.check_win(b)
		return (board,win,winner)

	def check_win(self,b):
		if b[0] != ' ':
			if b[0] == b[1] and b[0] == b[2]:
				return (True,b[0])
			if b[0] == b[3] and b[0] == b[6]:
				return (True,b[0])
		if b[4] != ' ':
			if b[0] == b[4] and b[0] == b[8]:
				return (True,b[4])
			if b[2] == b[4] and b[2] == b[6]:
				return (True,b[4])
			if b[1] == b[4] and b[1] == b[7]:
				return (True,b[4])
			if b[3] == b[4] and b[3] == b[5]:
				return (True,b[4])
		if b[8] != ' ':
			if b[2] == b[8] and b[2] == b[5]:
				return (True,b[8])
			if b[6] == b[8] and b[6] == b[7]:
				return (True,b[8])
		return (False,None)


	def tictac3d(self,socklist,addrlist):
		print 'three users in a match'
		for sock in socklist:
			try:
				sock.sendall('match can begin')
			except:
				print 'a player has left'
				return
		#while 1 and not self.event.is_set():
		while 1:
			sleep(.1)
			
			ready_to_read,ready_to_write,in_error = select.select(socklist,[],[],0)
			for sock in ready_to_read:
				addr = addrlist[socklist.index(sock)]

				try:
					data = sock.recv(1024)
				except:
					print 'a bad playa disconnected, game disbanded $%$%$'
					return
				if data:
					sock.sendall('message received')
					for sock2 in socklist:
						if sock != sock2:
							try:
								sock2.sendall(data)
							except:
								'a poor player has left, game disbanded'
								return

	def tictac2dthread(self):
		while 1:
			sleep(0.1)
			while len(self.socketlist2d) >= 2:
				playersReady = 0
				for sock in self.socketlist2d[0:2]:
					sock.sendall('ready?')
					try:
						response = sock.recv(16)
					except:
						print 'A player has disconnected from the 2d queue'
					if response:
						playersReady += 1
					else:
						if sock in self.socketlist2d:
							self.addrlist2d.remove(self.addrlist2d[self.socketlist2d.index(sock)])
							self.socketlist2d.remove(sock)
							print 'A player has disconnected from the 2d queue (2nd option)'
				if playersReady == 2:
					print 'a game can begin'

					tictac2dgame = threading.Thread(target=self.tictac2d,args=(self.socketlist2d[0:2],self.addrlist2d[0:2]))
					tictac2dgame.daemon = True
					tictac2dgame.start() #starts tictac2d thread

					del self.socketlist2d[0:2]
					del self.addrlist2d[0:2]
				else:
					print 'a game can not begin; player count is only %s' % str(playersReady)
					for sock in self.socketlist2d:
						sock.sendall('waiting for additional players')

	def tictac3dthread(self):
		while 1:
			sleep(0.1)
			while len(self.socketlist3d) >= 3:
				playersReady = 0
				for sock in self.socketlist3d[0:3]:
					sock.sendall('ready?')
					try:
						response = sock.recv(16)
					except:
						print 'A player has disconnected from the 3d queue'
					if response:
						playersReady += 1
					else:
						if sock in self.socketlist3d:
							self.addrlist3d.remove(self.addrlist3d[self.socketlist3d.index(sock)])
							self.socketlist3d.remove(sock)
							print 'A player has disconnected from the 3d queue (3nd option)'
				if playersReady == 3:
					print 'a game can begin'

					tictac3dgame = threading.Thread(target=self.tictac3d,args=(self.socketlist3d[0:3],self.addrlist3d[0:3]))
					tictac3dgame.daemon = True
					tictac3dgame.start() #starts tictac3d thread

					del self.socketlist3d[0:3]
					del self.addrlist3d[0:3]
				else:
					print 'a game can not begin; player count is only %s' % str(playersReady)
					for sock in self.socketlist3d:
						sock.sendall('waiting for additional players')



	def playerqueue2d(self,s,addr):
		self.socketlist2d.append(s)
		self.addrlist2d.append(addr)
		print "2d socket list: " + str(self.socketlist2d)
		print "2d addr list: " + str(self.addrlist2d)		

		#for sock in self.socketlist2d:
		#	sock.sendall('waiting for additional players')
				
		#if len(self.socketlist2d) >= 2:
		#	for sock in self.socketlist2d[0:2]
		#	userthread = threading.Thread(target=self.tictac2d,args=(self.socketlist2d,self.addrlist2d))
		#	userthread.daemon = True
		#	userthread.start()
		#	self.socketlist2d = []
		#	self.addrlist2d = []


	def playerqueue3d(self,s,addr):
		self.socketlist3d.append(s)
		self.addrlist3d.append(addr[0])
		print "3d socket list: " + str(self.socketlist3d)
		print "3d addr list: " + str(self.addrlist3d)	

	def distinguishCommand(self,s,addr,AESkey):
		order = s.recv(128)
		print 'command is: %s' % order

		if order == '2d':
			s.send('ok')
			print 'command understood, performing: %s' % order
			self.playerqueue2d(s,addr)
		elif order == '3d':
			s.send('ok')
			print 'command understood, performing: %s' % order
			self.playerqueue3d(s,addr)
		else: # unknown command
			s.send('no')
			print 'command not understood'

	def netPass_check(self,s,AESkey):
		netPass = self.netPass
		s.sendall('yp')
		has = s.recv(1)
		s.sendall('ok')
		if has != 'y':
			print "does not have proper password"
			s.close
			return False
		else:
			#cliPass = s.recv(512)
			cliPass = self.recvTem(s,512,AESkey)
			if cliPass != netPass:
				s.sendall('n')
				print "does not have proper password"
				s.close
				return False
			else:
				s.sendall('y')
				return True

	def servergen(self):
		global version
		print 'tic tac server started - version %s on port %s\n' % (version,self.serverport)
		self.get_netPass()
		netPass = self.netPass
		# create a socket object
		serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		socketlist = []
		# get local machine name
		host = ""
		port = self.serverport

		# bind to the port
		serversocket.bind((host, port))

		# queue up to 10 requests
		serversocket.listen(10)
		socketlist.append(serversocket)

		while 1 and not self.event.is_set():
			sleep(.1)
			
			ready_to_read,ready_to_write,in_error = select.select(socketlist,[],[],0)

			for sock in ready_to_read:
				# establish a connection
				if sock == serversocket:
					s,addr = serversocket.accept()
					print("Got a connection from %s" % str(addr))
					try:
						AESkey = None
						client_enc = s.recv(2)
						print client_enc
						if client_enc == 'en':
							if self.shouldEncrypt == True:
								print "going through encryption route"
								s.sendall('ye')
								key_to_send = self.pubkey.exportKey('PEM')
								s.recv(1)
								s.sendall(key_to_send)
								ciphertext = s.recv(1024)
								cipher = PKCS1_OAEP.new(self.key)
								AESkey = cipher.decrypt(ciphertext)
								print("AES key received")
							else:
								print "not going through encryption route"
								s.sendall('ne')
								s.recv(2)
						else:
							pass

						if netPass != None:
							print "checking netpass..."
							rightPass = self.netPass_check(s,AESkey)
						else:
							rightPass = True
							s.sendall('np')

						if rightPass == True:
							#identity = s.recv(1024)
							identity = self.recvTem(s,1024,AESkey)
							compat = 'n'
							scriptname,function,cli_version = identity.split(':')
							if scriptname == 'tictac' and function == 'tictac_client' and cli_version == version:
								compat = 'y'

							s.sendall(compat)

							if compat != 'y': #not a master, so respond with 
								s.recv(2)
								#s.sendall('n|master:master_function:%s|' % version)
								self.sendTem(s,'n|tictac:tictac_client:%s|' % version,AESkey)
								print 'does not have protocol'
								s.close
							else:
								print 'HAS protocol'
								s.recv(2)
								s.sendall('ok')
								self.distinguishCommand(s,addr,AESkey)
								#syncthread = threading.Thread(target=distinguishCommand,args=(s,))
								#syncthread.daemon = True
								#syncthread.start()

								s.close
							print("Disconnection by %s with data received" % str(addr))

					except Exception,e:
						print str(e) + '\n'
		self.exit()


	def servergenOLD(self):
		global version
		print 'tic tac server started - version %s on port %s\n' % (version,self.serverport)
		self.get_netPass()
		netPass = self.netPass
		# create a socket object
		serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		socketlist = []
		# get local machine name
		host = ""
		port = self.serverport

		# bind to the port
		serversocket.bind((host, port))

		# queue up to 10 requests
		serversocket.listen(10)
		socketlist.append(serversocket)

		while 1 and not self.event.is_set():
			sleep(.1)
			
			ready_to_read,ready_to_write,in_error = select.select(socketlist,[],[],0)

			for sock in ready_to_read:
				# establish a connection
				if sock == serversocket:
					clientsocket,addr = serversocket.accept()
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
							if scriptname == 'tictac' and function == 'tictac_client' and cli_version == version:
								compat = 'y'

							clientsocket.sendall(compat)

							if compat != 'y': #not a sync_client, so respond with 
								clientsocket.recv(2)
								clientsocket.sendall('n|tictac:tictac_client:%s|' % version)
								print 'does not have protocol'
								clientsocket.close
							else:
								print 'HAS protocol'
								clientsocket.recv(2)
								clientsocket.sendall('ok')
								self.distinguishCommand(clientsocket,addr)

								clientsocket.close
							print("Disconnection by %s with data received" % str(addr))

					except Exception,e:
						print str(e) + '\n'
		self.exit()

	def clear(self): #clear screen, typical way
		if os.name == 'nt':
			os.system('cls')
		else:
			os.system('clear')

	def exit(self): #kill all proceses for a tidy exit
		quit()

	def sendTem(self,s,msg,key = None): #msg = string
		if key != None:
			iv = Random.new().read(AES.block_size)
			cipher = AES.new(key, AES.MODE_CFB, iv)
			ciphertext = iv + cipher.encrypt(msg)
			s.sendall(ciphertext+"ENDING")
		else:
			return s.sendall(msg)

	def recvTem(self,s,bytes,key = None): #bytes = integer
		if key != None:
			amount = 16+6+bytes
			recvd = 0
			ciphertext = ""
			while True:
				cipherpart = s.recv(amount)
				recvd += len(cipherpart)
				ciphertext += cipherpart
				if ciphertext[-6:] == "ENDING":
					break
			if ciphertext == "":
				return ""
			iv = ciphertext[:16]
			cipher = AES.new(key, AES.MODE_CFB, iv)
			return cipher.decrypt(ciphertext[16:-6])
		else:
			received = s.recv(bytes)
			return received

def mainclass(inp=None):
	if inp == None:
		return TicTacServer()
	else:
		return TicTacServer(inp)

def main(argv):
	portS = None
	try:
		opts,args = getopt.getopt(argv, 'p:',['port='])
	except getopt.GetoptError:
		print '-p [port] or --port [port] only'
		quit()
	for opt, arg in opts:
		if opt in ("-p","--port"):
			portS = arg
	if portS == None:
		program = TicTacServer().start()
	else:
		try:
			portI = int(portS)
		except ValueError:
			print 'port must be an integer'
		else:
			program = TicTacServer(portI).start()

if __name__ == '__main__':
	main(sys.argv[1:])