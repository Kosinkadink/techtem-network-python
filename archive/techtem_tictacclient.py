#!/usr/bin/python2
import sys, socket, select, os, threading
from time import strftime, sleep, time
from hashlib import sha1, md5
from getpass import getpass
try:
	from Crypto.Cipher import AES
	from Crypto import Random
	from Crypto.PublicKey import RSA
	from Crypto.Cipher import PKCS1_OAEP
except ImportError:
	print "NOTICE: PyCrypto not found on Python 2.7; try the command 'pip install pycrypto' or find the package online"
	raw_input("Connections will NOT be encrypted. Press ENTER to continue.")

#universal variables
__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__))) #directory from which this script is ran
if os.name == 'nt':
	__location__ = __location__.replace('\\','/')
version = '2.0.test003'
#script-specific variables

class TicTacClient(object):

	netPass = None
	password = None
	username = None
	send_cache = 40960
	send_cache_enc = 40960
	should_encrypt = False
	AES_keysize = 32 #16, 24, 32

	def __init__(self):
		self.initialize()

	def run_processes(self):
		self.serverterminal()

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
		#sync files start
		if not os.path.exists(__location__+'/resources/programparts/sync'): os.makedirs(__location__+'/resources/programparts/sync')

		if not os.path.exists(__location__+'/resources/programparts/sync/serverlist.txt'):
			with open(__location__+'/resources/programparts/sync/serverlist.txt', "a") as seeds:
				seeds.write("""####################################################
##The format is: ||ip:port||
##Files will be sent to and from these servers
##Only lines starting with || will be read
####################################################""")
		#sync files end

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

	def boot(self):
		self.clear()
		print "TechTem Sync Client started"
		print "Version " + version
		print "Type help for command list\n"

	def help(self):
		print "\nclear: clears screen"
		print "exit: closes program"
		print "time: receive server time"
		print "newacc: create new account on server"
		print "createsync: create a new sync state"
		print "sync: sync client files with server"
		print "login: set username and password for client"
		print "size: check size of user directory client-side"
	#function for client splash screen
	def serverterminal(self):
		self.boot()
		while 1:
			inp = raw_input("")
			if inp:
				if inp.split()[0] == 'quit' or inp.split()[0] == 'leave' or inp.split()[0] == 'exit':
					self.exit()
				elif inp.split()[0] == 'clear':
					self.boot()
				elif inp.split()[0] == 'encrypt':
					if self.should_encrypt:
						self.should_encrypt = False
						print "Encryption is now OFF"
					else:
						try:
							Random.new()
						except NameError:
							print "PyCrypto NOT imported; encryption not available"
						else:
							self.should_encrypt = True
							print "Encryption is now ON"
				elif inp.split()[0] == 'time':
					self.connectTime()
				elif inp.split()[0] == 'help' or inp.split()[0] == '?':
					self.help()
				elif inp.split()[0] == 'login':
					self.login()
				elif inp.split()[0] == 'newacc':
					self.connectCreateNew()
				elif inp.split()[0] == 'check':
					self.connectCheckAuth()
				elif inp.split()[0] == 'createsync':
					self.createSyncState()
				elif inp.split()[0] == 'sync':
					self.connectSync()
				elif inp.split()[0] == 'size':
					self.checkSize()
				elif inp.split()[0] == 'sum':
					self.checkChecksum(inp.split()[1])
				elif inp.split()[0] == 'netpass':
					self.get_netPass()
					print self.netPass
				else:
					print "Invalid command"

	def checkSize(self):
		username = raw_input("Username: ")
		try:
			start = time()
			print self.sizeDir(__location__ + '/resources/programparts/sync/%s' % username.lower())
			end = time()
			print str(end-start)
		except Exception,e:
			print str(e)

	def userSize(self,username):
		return str(self.sizeDir(__location__ + '/resources/programparts/sync/%s' % username.lower()))

	def checkChecksum(self, type):
		username = raw_input("Username: ")
		try:
			if type == 'md':
				start = time()
				list = self.checksumList(__location__ + '/resources/programparts/sync/%s' % username.lower(), 'md')
				end = time()
				print list
				print str(end-start)

			elif type == 'sh':
				start = time()
				list = self.checksumList(__location__ + '/resources/programparts/sync/%s' % username.lower(), 'sh')
				end = time()
				print list
				print str(end-start)
		except Exception,e:
			print str(e)

	def createSyncState(self):
		try:
			valid = self.connectCheckAuth()
			if not valid:
				raise ValueError("authentication error")
			username = self.username
			if not os.path.exists(__location__+'/resources/programparts/sync/%s' % username):
				os.makedirs(__location__+'/resources/programparts/sync/%s' % username)
				with open(__location__+'/resources/programparts/sync/%s/timestamp.txt' % username, "a") as timedoc:
					timedoc.write("""00000000000000""")
			else:
				if not os.path.exists(__location__+'/resources/programparts/sync/%s/timestamp.txt' % username):
					with open(__location__+'/resources/programparts/sync/%s/timestamp.txt' % username, "a") as timedoc:
						timedoc.write("""00000000000000""")
				else:
					os.remove(__location__+'/resources/programparts/sync/%s/timestamp.txt' % username)
					timestamp = self.connectTime()
					with open(__location__+'/resources/programparts/sync/%s/timestamp.txt' % username, "a") as timedoc:
						timedoc.write(timestamp)
			print 'Creating sync state...'
			with open(__location__+'/resources/programparts/sync/%s/timestamp.txt' % username, "a") as timedoc:
				list = self.checksumList(__location__ + '/resources/programparts/sync/%s' % username.lower(), 'sh')
				for item in list:
					timedoc.write('\n' + item)
			print 'Sync state created.'
		except Exception,e:
			print str(e) + '\n'

	def connectSync(self):
		try:
			valid = self.connectCheckAuth()
			if not valid:
				return
			username = self.username
			if not os.path.exists(__location__+'/resources/programparts/sync/%s' % username):
				os.makedirs(__location__+'/resources/programparts/sync/%s' % username)
				with open(__location__+'/resources/programparts/sync/%s/timestamp.txt' % username, "a") as timedoc:
					timedoc.write("""00000000000000""")
			else:
				if not os.path.exists(__location__+'/resources/programparts/sync/%s/timestamp.txt' % username):
					with open(__location__+'/resources/programparts/sync/%s/timestamp.txt' % username, "a") as timedoc:
						timedoc.write("""00000000000000""")
			dirSize = self.userSize(username)
			print self.connectToServer('spec' + dirSize,'sync')

		except Exception,e:
			print str(e) + '\n'

	def login(self):
		username = self.username
		password = self.password
		try:
			self.username = raw_input("Username: ").lower()
			self.password = getpass("Password: ")
			# make sure lengths are okay
			if len(self.username) < 19 and len(self.password) < 129:
				print "Username and Password entered"
				return True
			else:
				print "Improper number of characters, try again."
				raise ValueError("incorrect # of characters")
		except Exception,e:
			print str(e)
			self.username = None
			self.password = None
			return False

	def loginnew(self):
		username = self.username
		password = self.password
		try:
			self.username = raw_input("Username: ").lower()
			self.password = getpass("Password: ")
			password2 = getpass("Re-enter Password: ")
			# make sure passwords match and lengths are okay
			if self.password == password2 and len(self.username) < 19 and len(self.password) < 129:
				print "Username and Password entered"
				return True
			else:
				print "Passwords do not match, try again."
				raise ValueError("password mismatch")
		except Exception,e:
			print str(e)
			self.username = None
			self.password = None
			return False

	def sizeDir(self,folder): # get size of directory and all subdirectories
		if os.name == 'nt':
			folder = folder.replace('\\','/')
		total_size = os.path.getsize(folder)
		for item in os.listdir(folder):
			itempath = os.path.join(folder, item)
			if os.path.isfile(itempath):
				total_size += os.path.getsize(itempath)
				#checksum(itempath)
			elif os.path.isdir(itempath):
				total_size += self.sizeDir(itempath)
		return total_size

	def checksumList(self,itempath,type):
		username = self.username
		folder = itempath
		checksumlist = []
		if type == 'md':
			for item in os.listdir(folder):
				itempath = os.path.join(folder, item)
				if os.name == 'nt':
					itempath = itempath.replace('\\','/')
				if os.path.isfile(itempath):
					gene = itempath.split(__location__ + '/resources/programparts/sync/%s/' % username)[1:]
					listLength = len(gene)
					if listLength > 1:
						actual = ''
						number = 0
						while number < listLength:
							actual += gene[number]
							if (number + 1) != listLength:
								actual += '/resources/programparts/sync/%s/' % username
					else:
						actual = gene[0]
					checksumlist += [actual+self.checksum(itempath)]
					#checksum(itempath)
				elif os.path.isdir(itempath):
					checksumlist += self.checksumList(itempath, type)
			return checksumlist
		elif type == 'sh':
			for item in os.listdir(folder):
				itempath = os.path.join(folder, item)
				if os.name == 'nt':
					itempath = itempath.replace('\\','/')
				if os.path.isfile(itempath):
					gene = itempath.split(__location__ + '/resources/programparts/sync/%s/' % username)[1:]
					listLength = len(gene)
					if listLength > 1:
						actual = ''
						number = 0
						while number < listLength:
							actual += gene[number]
							if (number + 1) != listLength:
								actual += __location__ + '/resources/programparts/sync/%s/' % username
					else:
						actual = gene[0]
					checksumlist += [actual+self.checksum2(itempath)]
					#checksum(itempath)
				elif os.path.isdir(itempath):
					checksumlist += self.checksumList(itempath, type)
			return checksumlist

	def checksum(self,itempath):
		if os.path.getsize(itempath) < 50240000:
			data = md5(open(itempath).read()).hexdigest()
			#print '[%s]' % data
			return '::' + data
		else:
			#print '['
			with open(itempath) as file:
				datamult = '::'
				while True:
					data = file.read(50240000)
					if data:
						data = md5(data).hexdigest()
						datamult += data
						#print data
					else:
						break
				#print ']' 
				#print 'Checksum complete.'
				return datamult

	def sizeDir2(self,folder): # get size of directory and all subdirectories
		total_size = os.path.getsize(folder)
		for item in os.listdir(folder):
			itempath = os.path.join(folder, item)
			if os.path.isfile(itempath):
				total_size += os.path.getsize(itempath)
				self.checksum2(itempath)
			elif os.path.isdir(itempath):
				total_size += self.sizeDir2(itempath)
		return total_size

	def checksum2(self,itempath):
		if os.path.getsize(itempath) < 50240000:
			data = sha1(open(itempath).read()).hexdigest()
			#print '[%s]' % data
			return '::' + data
			
		else:
			#print '['
			with open(itempath) as file:
				datamult = '::'
				while True:
					data = file.read(50240000)
					if data:
						data = sha1(data).hexdigest()
						datamult += data
						#print data
					else:
						break
				#print ']' 
				#print 'Checksum complete.'
				return datamult
			

	def connectCheckAuth(self):
		#global username, password
		try:
			valid = self.login()
			if valid:
				pass
			if not valid:
				raise ValueError("login entry error")
			return self.connectToServer('checkAuth','checkauth')

		except Exception,e:
			print str(e) + '\n'

	def connectCreateNew(self):
		#global username, password
		try:
			valid = self.loginnew()
			if valid:
				pass
			if not valid:
				raise ValueError("login entry error")
			self.connectToServer('createAccount','newuser')

		except Exception,e:
			print str(e) + '\n'

	def connectTime(self):
		time = self.connectToServer('savedtime','time')
		print time
		return time

	def connectToServer(self,data,command):
		with open(__location__+'/resources/programparts/sync/serverlist.txt', "r") as seeds:
			for line in seeds:
				if line.startswith('||'):
					#try: #connect to ip, save data, issue command
					return self.connectip(line.split("||")[1],data,command)
					#except Exception,e:
					print str(e) + "\n"
		print ''

	def connectip(self,ip,data,command): #connect to ip
		try:
			host = ip.split(':')[0]
			port = int(ip.split(':')[1])
		except:
			return 'invalid host/port provided\n'
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.settimeout(5)
		try:
			s.connect((host, port))
		except:
			s.close
			return "Seed at " + ip + " not available\n"
		print "\nConnection successful to " + ip
		return self.connectprotocolclient(s,data,command)

	def sendItem(self,s,AESkey = None): #send file to seed

		start = time()
		username = self.username
		#gene = s.recv(1024)
		gene = self.recvTem(s,1024,AESkey)
		print 'sending data'
		print 'awaiting reply'

		file_name = gene.split('/')[-1]

		file = __location__ + '/resources/programparts/sync/%s/' % username + gene

		#print os.path.join(uploads, file_name)
		print file
		if os.path.exists(file):
			print file_name + " found"
			s.sendall('ok')

			use_cache = self.recvTem(s,16,AESkey)
			use_cache = int(use_cache.strip())

			filelength =  os.path.getsize(file)
			#s.sendall('%16d' % filelength)
			self.sendTem(s,'%16d' % filelength,AESkey)
			s.recv(2)
			with open(file, 'rb') as f:
				print file_name + " sending..."
				sent = 0
				while True:
					try:
						sys.stdout.write(str((float(sent)/filelength)*100)[:4]+ '%   ' + str(sent) + '/' + str(filelength) + ' B\r')
						sys.stdout.flush()
					except:
						pass
					data = f.read(use_cache)
					if not data:
						break
					sent += len(data)
					#s.sendall(data)
					self.sendTem(s,data,AESkey)
			s.recv(2)
			sys.stdout.write('100.0%   ' + str(sent) + '/' + str(filelength) + ' B\n')
			print file_name + " sending successful"
			
		else:
			print file_name + " not found"
			s.sendall('no')

	def sendTimestamp(self,s,AESkey = None): #send file to seed
		username = self.username
		data = __location__+'/resources/programparts/sync/%s/timestamp.txt' % username
		if os.name == 'nt':
			data = data.replace('\\','/')
		print 'sending data'
		dataloc = __location__
		if os.name == 'nt':
			dataloc = dataloc.replace('\\','/')							   
		s.sendall(dataloc+'/resources/programparts/sync/%s/timestampclient.txt' % username)
		print 'awaiting reply'
		s.recv(2)

		file = data

		uploads = __location__ + '/resources/uploads/'

		file_name = data.split('/')[-1]

		print file
		if os.path.exists(file):
			print file_name + " found"
			s.sendall('ok')
			s.recv(2)

			filelength =  os.path.getsize(file)
			s.sendall('%16d' % filelength)
			with open(file, 'rb') as f:
				print file_name + " sending..."
				sent = 0
				while True:
					sys.stdout.write(str((float(sent)/filelength)*100)[:4]+ '%' + '\r')
					sys.stdout.flush()
					data = f.read(10240)
					if not data:
						break
					sent += len(data)
					s.sendall(data)

			s.recv(2)
			sys.stdout.write('100.0%\n')
			print file_name + " sending successful"
			
		else:
			print file_name + " not found"

	def sendFileList(self,s,files,AESkey = None): #send file list
		data = files
		s.sendall('%16d' % len(data))
		print "file list sending..."
		s.sendall(data)
		s.recv(2)
		print "file list sending successful"

	def sendCommand(self,s,data,AESkey = None): #send sync files to server
		username = self.username
		folder = __location__+'/resources/programparts/sync/%s/' % username

		if data == 'sync':
			filessent = self.sendSyncFiles(s, folder)
			print filessent
			s.sendall('n')
			s.recv(2)
			files = '@%$%@'
			for fileloc in filessent:
				files += fileloc + '@%$%@'
			self.sendFileList(s, files)
		elif data == 'spec':
			self.sendSpecFiles(s, AESkey)
		else:
			s.sendall('n')
			return 'unknown response'

	def sendSyncFiles(self,s, folder,AESkey = None):

		#total_size = os.path.getsize(folder)
		syncedfiles = []
		for item in os.listdir(folder):
			itempath = os.path.join(folder, item)
			if os.name == 'nt':
				itempath = itempath.replace('\\','/')
			if os.path.isfile(itempath):
				syncedfiles += [itempath]
				s.sendall('y')
				s.recv(2)
				self.sendItem(s,itempath)
			elif os.path.isdir(itempath):
				syncedfiles += self.sendSyncFiles(s, itempath)
		return syncedfiles

	def sendSpecFiles(self,s,AESkey = None):
		username = self.username
		s.sendall('ok')
		s.recv(2)
		while True:
			s.sendall('ok')
			sending = s.recv(1)
			if sending == 'y':
				s.sendall('ok')
				print 'receiving location...'
				self.sendItem(s, AESkey)
			else:
				break
		pass

	def recvSpecFiles(self,s,AESkey = None):
		username = self.username
		s.sendall('ok')
		s.recv(2)
		while True:
			s.sendall('ok')
			sending = s.recv(1)
			if sending == 'y':
				s.sendall('ok')
				self.sync_recv_file(s, username,AESkey)
			else:
				break
		pass

	def receiveSyncCommand(self,s, data,AESkey = None):
		username = self.username
		self.recvSpecFiles(s,AESkey)
		files = []
		with open(__location__+'/resources/programparts/sync/%s/timestamp.txt' % username, 'rb') as timedoc:
			for line in timedoc:
				files += [line]
		files = files[1:]
		#print files
		folder = __location__+'/resources/programparts/sync/%s/' % username
		if os.name == 'nt':
			folder = folder.replace('\\','/')	

		filelist = []
		for file in files:
			#print file
			file = file.split('::')[0]
			file = folder + file
			filelist += [file]

		self.removeUnsyncedFiles(s, folder, filelist)

	def receiveCommand(self,s, data,AESkey = None): # loops receiving files until master denies
		username = self.username
		while True:
			sending = s.recv(1)
			s.sendall('ok')
			if sending == 'y':
				self.sync_recv_file(s, username)
			else:
				break
		s.sendall('ok')
		files = self.recv_file_list(s,AESkey)
		files = files.split('@%$%@')[1:-1]
		folder = __location__+'/resources/programparts/sync/%s/' % username
		print folder
		if os.name == 'nt':
			folder = folder.replace('\\','/')
		localfiles = []
		print folder
		for file in files:
			splitfile = file.split('/resources/programparts/sync/%s/' % username)[1]
			localfiles += [folder + splitfile]
		print localfiles
		print 'location: %s' % __location__
		print 'folder: %s' % folder
		self.removeUnsyncedFiles(s, folder, localfiles)

	def removeUnsyncedFiles(self,s, folder, files):
		#total_size = os.path.getsize(folder)
		syncedfiles = []
		for item in os.listdir(folder):
			itempath = os.path.join(folder, item)
			if os.name == 'nt':
				itempath = itempath.replace('\\','/')
			if os.path.isfile(itempath):
				syncedfiles += [itempath]
				if not itempath in files:
					print 'removing %s' % itempath
					os.remove(itempath)
			elif os.path.isdir(itempath):
				syncedfiles += self.removeUnsyncedFiles(s, itempath, files)

		self.removeUnsyncedFolders(folder)

		return syncedfiles

	def removeUnsyncedFolders(self,folder):
		files = os.listdir(folder)
		#remove empty subfolders
		if len(files):
			for f in files:
				#if os.name == 'nt':
				#	f = f.replace('\\','/')
				fullpath = os.path.join(folder, f)
				if os.path.isdir(fullpath):
					self.removeUnsyncedFolders(fullpath)
		#if folder empty, delete it
		files = os.listdir(folder)
		if len(files) == 0:
			os.rmdir(folder)

	def sync_recv_file(self,s, username,AESkey = None): #receives files from client
		#gene = s.recv(1024)
		gene = self.recvTem(s,1024,AESkey)
		s.send('ok')
		print gene
		filelocpre = gene.split('/resources/programparts/sync/%s/' % username, 1)[1]
		filename = filelocpre.split('/')[-1]
		filelocpre = filelocpre.split('/')[:-1]
		fileloc = ''
		for file in filelocpre:
			fileloc += file + '/'

		downloadslocation = __location__ + '/resources/programparts/sync/%s/' % username + fileloc

		has = s.recv(2)
		if has != 'ok':
			return '404'
		else:
			#s.sendall('ok')
			file_cache = self.recvTem(s,16,AESkey)
			file_cache = int(file_cache.strip())

			s.sendall('ok')
			#size = s.recv(16)
			size = self.recvTem(s,16,AESkey)
			size = int(size.strip())
			s.sendall('ok')
			recvd = 0
			print filename + ' download in progress...'
			if not os.path.exists(downloadslocation):
				os.makedirs(downloadslocation)
			q = open(os.path.join(downloadslocation, filename), 'wb')
			while size > recvd:
				sys.stdout.write(str((float(recvd)/size)*100)[:4]+ '%' + '\r')
				sys.stdout.flush()
				#data = s.recv(file_cache)
				data = self.recvTem(s,file_cache,AESkey)
				if not data: 
					break
				recvd += len(data)
				q.write(data)
			s.sendall('ok')
			q.close()
			sys.stdout.write('100.0%\n')
			print filename + ' download complete'
			return '111'

	def recv_file_list(self,s,AESkey): #receives files from client

		size = s.recv(16)
		size = int(size.strip())
		recvd = 0
		print  'file names download in progress...'
		list = ''
		while size > recvd:
			sys.stdout.write(str((float(recvd)/size)*100)[:4]+ '%' + '\r')
			sys.stdout.flush()
			data = s.recv(1024)
			if not data: 
				break
			recvd += len(data)
			list += data
		s.sendall('ok')
		sys.stdout.write('100.0%\n')
		print 'file names download complete'
		return list

	def isValidSize(self,s, size_dir, AESkey = None):
		s.sendall(size_dir)
		valid = s.recv(1)
		if valid == 'y':
			return True
		else:
			return False
		

	def syncCommand(self,s, data,AESkey = None):
		size_dir = data[4:]
		data = data[:4]
		valid = self.checkAuthCommand(s, data, AESkey)
		if not valid:
			return "authentication error"
		#with open(__location__+'/resources/programparts/sync/%s/timestamp.txt' % username, "rb") as timedoc:
		#	timestamp = timedoc.readline()
		self.sendTimestamp(s, AESkey)

		print size_dir
		valid = self.isValidSize(s, size_dir, AESkey)
		if not valid:
			s.send('ok')
			response = s.recv(1024)
			return response
		s.send('ok')
		
		works = s.recv(2)
		if works != 'ok':
			s.sendall('ok')
			response = s.recv(128)
			return response
		s.sendall('ok')
		action = s.recv(4)
		if action == 'send':
			self.sendCommand(s, data, AESkey)
			return 'Sync complete.'
		elif action == 'recv':
			self.receiveSyncCommand(s, data, AESkey)
			return 'Sync complete.'
		elif action == 'same':
			return 'already synced'

	def checkAuthCommand(self,s, data,AESkey = None):
		username = self.username
		password = self.password
		#s.sendall(username)
		self.sendTem(s,username,AESkey)
		valid = s.recv(1)
		if valid == 'n':
			print 'Username is invalid'
			return False
		#s.sendall(password)
		self.sendTem(s,password,AESkey)
		match = s.recv(1)
		if match == 'y':
			print 'Correct Username/Password Combo'
			return True
		else:
			print 'Incorrect Username/Password Combo'
			return False

	def newUserCommand(self,s, data,AESkey = None):
		username = self.username
		password = self.password
		s.send(username)
		proper = s.recv(1)
		if proper == 'y':
			s.send(password)
			response = s.recv(1)
			if response == 'y':
				s.send('ok')
				print 'Account created.'
				if not os.path.exists(__location__+'/resources/programparts/sync/%s' % username):
					os.makedirs(__location__+'/resources/programparts/sync/%s' % username)
					with open(__location__+'/resources/programparts/sync/%s/timestamp.txt' % username, "a") as timedoc:
						timedoc.write("""00000000000000""")
				else:
					if not os.path.exists(__location__+'/resources/programparts/sync/%s/timestamp.txt' % username):
						with open(__location__+'/resources/programparts/sync/%s/timestamp.txt' % username, "a") as timedoc:
							timedoc.write("""00000000000000""")
			else:
				s.send('ok')
				print s.recv(128)
		else:
			s.send('ok')
			print s.recv(128)

	def timeCommand(self,s, data, AESkey = None):
		s.sendall('send')
		time = s.recv(128)
		return time

	def distinguishCommand(self,ser, data, command,AESkey = None): #interpret what to tell seed
		if command == 'sync':
			order = 'sync'
			ser.sendall(order)
			understood = ser.recv(2)
			if understood == 'ok':
				print 'command: %s understood by seed' % order
				return self.syncCommand(ser, data,AESkey)
			else:
				print 'command not understood by seed'
		elif command == 'time':
			order = 'time'
			ser.sendall(order)
			understood = ser.recv(2)
			if understood == 'ok':
				print 'command: %s understood by seed' % order
				return self.timeCommand(ser, data,AESkey)
			else:
				print 'command not understood by seed'
		elif command == 'newuser':
			order = 'newuser'
			ser.sendall(order)
			understood = ser.recv(2)
			if understood == 'ok':
				print 'command: %s understood by seed' % order
				return self.newUserCommand(ser, data,AESkey)
			else:
				print 'command not understood by seed'
		elif command == 'checkauth':
			order = 'checkauth'
			ser.sendall(order)
			understood = ser.recv(2)
			if understood == 'ok':
				print 'command: %s understood by seed' % order
				return self.checkAuthCommand(ser, data,AESkey)
			else:
				print 'command not understood by seed'

	def connectprotocolclient(self,s, data, command): #communicate via protocol to command seed
		global version
		netPass = self.netPass
		self.get_netPass()
		AESkey = None

		if self.should_encrypt:
			s.sendall('en')
			server_enc = s.recv(2)
			print server_enc
			if server_enc not in ['ye','ne']: #would happen if server is not programmed to use encryption
				hasPass = server_enc
			else: #is not ancient (hehe)
				if server_enc == 'ne':
					s.sendall('ok')
					hasPass = s.recv(2)
				else: #receive public RSA, share AES key
					print "going through encryption route"
					AESkey = self.gen_AES_key()
					s.sendall('y')
					public_key = s.recv(1024)
					key = RSA.importKey(public_key)
					cipher = PKCS1_OAEP.new(key)
					ciphertext = cipher.encrypt(AESkey)
					s.sendall(ciphertext)
					enable_encryp = True
					hasPass = s.recv(2)
		else:
			s.sendall('ok')
			hasPass = s.recv(2)
		if hasPass == 'yp':
			if self.netPass == None:
				s.sendall('n')
				s.close
				return 'requires password'
			else:
				s.sendall('y')
				s.recv(2)
				#s.sendall(self.netPass)
				self.sendTem(s,self.netPass,AESkey)
				right = s.recv(1)
				if right != 'y':
					s.close
					return 'incorrect password'

		s.sendall('sync:sync_client:%s' % version) #check if sync_client is connecting
		compat = s.recv(1)

		if compat == 'y':
			s.sendall('ok')
			s.recv(2)
			print 'success initiated'
			return self.distinguishCommand(s, data, command, AESkey)

		else:
			s.sendall('ok')
			#resp = s.recv(1024)
			resp = self.recvTem(s,1024,AESkey)
			s.close
			print 'failure. closing connection...'
			return resp

		s.close
		return 'connection closed'

	def clear(self): #clear screen, typical way
		if os.name == 'nt':
			os.system('cls')
		else:
			os.system('clear')

	def exit(self):
		quit()

	def gen_AES_key(self):
		return Random.new().read(self.AES_keysize)

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

if __name__ == '__main__':
	program = TicTacClient()