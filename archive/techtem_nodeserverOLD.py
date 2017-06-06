#!/usr/bin/python2
import sys, socket, select, os, threading, getopt
from time import strftime, sleep

#initialization of the server
__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__))) #directory from which this script is ran
if os.name == 'nt':
	__location__ = __location__.replace('\\','/')
version = '2.0test003'
#script-specific variables

class NodeServer(threading.Thread):

	netPass = None
	serverport = 9025
	serverports = []
	threads = []
	send_cache = 40960
	send_cache_enc = 40960
	RSA_bitlength = 2048
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

	def help(self):
		print "\nclear - clears screen"
		print "help - displays this window"
		print "exit - close seed"

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

	def connectip_request(self,ip):
		try:
			host = ip.split(':')[0]
			port = int(ip.split(':')[1])
		except:
			return 'no host/port provided\n'
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.settimeout(3)
		try:
			s.connect((host, port))
			return (True,s)
		except:
			return (False,"Server at " + ip + " not available")

	def dConnectCommand(self,s,AESkey):
		ip = self.recvTem(s,32,AESkey)
		connected,q = self.connectip_request(ip)
		if not connected:
			s.sendall("no")
			s.recv(2)
			s.sendall(q)
		else:
			s.sendall("ye")
			socklist = [p,q]
			while True:
				sleep(.1)
				ready_to_read,ready_to_write,in_error = select.select(socklist,[],[],0)
				for sock in ready_to_read:
					if sock == p:
						pass
					elif sock == q:
						pass

	def connectCommand(self,s,AESkey):
		pass

	def distinguishCommand(self,s,AESkey = None): # interpret what master requests
		order = s.recv(128)
		print 'command is: %s' % order

		if order == 'connect': # sync
			s.send('ok')
			print 'command understood, performing: %s' % order
			self.connectCommand(s,AESkey)
		elif order == 'dconnect':
			s.send('ok')
			print 'command understood, performing: %s' % order
			self.dConnectCommand(s,AESkey)

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
		print 'node server started - version %s on port %s\n' % (version,self.serverport)
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
							identity = s.recv(1024)
							compat = 'n'
							scriptname,function,cli_version = identity.split(':')
							if scriptname == 'node' and function == 'node_function' and cli_version == version:
								compat = 'y'

							s.sendall(compat)

							if compat != 'y': #not a sync_client, so respond with 
								s.recv(2)
								#s.sendall('n|sync:sync_client:%s|' % version)
								self.sendTem(s,'n|node:node_function:%s|' % version,AESkey)
								print 'does not have protocol'
								s.close
							else:
								print 'HAS protocol'
								s.recv(2)
								s.sendall('ok')
								nodethread = threading.Thread(target=self.distinguishCommand,args=(s,AESkey))
								nodethread.daemon = True
								nodethread.start()

								s.close
							print("Disconnection by %s with data received" % str(addr))

					except Exception,e:
						print str(e) + '\n'
		self.exit()

	def clear(self): #clear screen, typical way
		if os.name == 'nt':
			os.system('cls')
		else:
			os.system('clear')

	def exit(self): #kill all processeses for a tidy exit
		#global threads
		#for operation in threads:
		#	operation._Thread_stop()
		#	print 'thread %s stopped successfully' % operation
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
				if cipherpart == "":
					break
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
		return NodeServer()
	else:
		return NodeServer(inp)

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
		program = NodeServer().start()
	else:
		try:
			portI = int(portS)
		except ValueError:
			print 'port must be an integer'
		else:
			program = NodeServer(portI).start()

if __name__ == '__main__':
	main(sys.argv[1:])