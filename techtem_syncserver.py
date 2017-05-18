#!/usr/bin/python2
import sys, socket, select, os, threading, subprocess, random, sqlite3, getopt, multiprocessing
from time import strftime, sleep, time
from hashlib import sha1, md5
from datetime import datetime

#initialization of the server
__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__))) #directory from which this script is ran
if os.name == 'nt':
	__location__ = __location__.replace('\\','/')
sys.path.insert(0, os.path.join(__location__,'resources/source/'))

#import common code
import CommonCode
import CommonCode_Server
CommonCode_Server.__location__ =  __location__

class TemplateServer(CommonCode_Server.TemplateServer):

	# don't change this
	netPass = None
	key = None
	pubkey = None
	threads = []
	pipes = []
	startTime = None
	saltlength = 16
	char = """ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890"""
	requireToken = True
	# change this to default values
	varDict = {
		"version": '3.0.0',
		"serverport": 9015,
		"useConfigPort": True,
		"send_cache": 409600,
		"scriptname": 'sync',
		"scriptfunction": 'sync_client',
		"name": 'sync',
		"downloadAddrLoc": 'jedkos.com:9011&&protocols/sync.py'
	}
	#form is ip:port&&location/on/filetransferserver/file.py

	#send_cache_enc = 40960
	#RSA_bitlength = 2048
	#shouldEncrypt = True
	#shouldEncryptDownload = True
	
	def __init__(self, serve=varDict["serverport"]):
		#self.__location__ = __location__
		CommonCode_Server.TemplateServer.__init__(self,serve)

	def init_spec(self):
		self.funcMap = {
		'sync':self.syncCommand,
		'time':self.timeCommand,
		'newuser':self.newUserCommand,
		'checkauth':self.checkAuthCommand,
		'size':self.sizeCommand
		}
		# insert application-specific initialization code here
		if not os.path.exists(__location__+'/resources/programparts/%s' % self.varDict["name"]): os.makedirs(__location__+'/resources/programparts/%s' % self.varDict["name"])
		if not os.path.exists(__location__+'/resources/programparts/sync/syncdatabase.sqlite3'):
			conn = sqlite3.connect(__location__+'/resources/programparts/sync/syncdatabase.sqlite3')
			cur = conn.cursor()
			cur.execute('CREATE TABLE Accounts (salt TEXT, username TEXT, password TEXT, sizelim INTEGER, isAvailable INTEGER, locations TEXT, synctimestamp INTEGER)')
			conn.close()
		if not os.path.exists(__location__+'/resources/programparts/sync/synclocations.txt'):
			with open(__location__+'/resources/programparts/sync/synclocations.txt', 'wb') as locations:
				locations.write("## write all locations as |ip:port|ip:port|...|\n")
		# create token server list
		if not os.path.exists(__location__+'/resources/programparts/%s/tokenservers.txt' % self.varDict["name"]):
			with open(__location__+'/resources/programparts/%s/tokenservers.txt' % self.varDict["name"],'wb') as tokenservs:
				tokenservs.write("## write an IP like this: ||ip:port||")


	def gen_Service_key(self):
		pass

	def serverterminal(self,inp): #used for server commands
		if inp:
			if inp == 'exit':
				self.exit()
			elif inp == 'clear':
				self.clear()
			elif inp == 'info':
				self.info()

	def loadClientClass(self,data): #used to start protocols not requiring connection
		print 'trying to load %s' % data
		try:
			scriptname = data
			compat = 'n'
			with open(__location__+'/resources/protocols/protlist.txt') as protlist:
				for line in protlist:
					print line
					if line == scriptname or line == scriptname + '\n' :
						compat = 'y'
						break

			if compat == 'y':
				script = sys.modules[scriptname]
				try:
					isAlone = getattr(script,'standalone')
				except:
					isAlone = False
				finally:
					if not isAlone:
						raise NameError('protocol is not specified as standalone')
				varcheck = getattr(script,'variables')
				if len(varcheck) <= len(data):
					function = getattr(script,'serverfunction')
					use = getattr(script,function)
					print 'success'
				else:
					raise NameError('incorrect argument[s]')
			else:
				raise NameError('failure - protocol not found')

			clientClass = use(__location__)
			print type(clientClass)
			print 'load success'
			return clientClass
		except Exception,e:
			print str(e)
			print 'load failed'
			return None

	def sync_recv_file(self,s, username, gene): #receives files from client

		s.sendall(gene)
		print gene
		filename = gene.split('/')[-1]
		filelocpre = gene.split('/')[:-1]
		fileloc = ''
		for file in filelocpre:
			fileloc += file + '/'

		downloadslocation = __location__ + '/resources/programparts/sync/%s/' % username + fileloc

		has = s.recv(2)
		if has != 'ok':
			return '404'
		else:
			#s.sendall('%16d' % self.send_cache)
			if s.getKey() == None:
				use_cache = self.send_cache
			else:
				use_cache = self.send_cache_enc

			s.sendall('%16d' % use_cache)
			#size = s.recv(16)
			size = s.recv(16)
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
				data = s.recv(use_cache)
				if not data: 
					break
				recvd += len(data)
				q.write(data)
			s.sendall('ok')
			q.close()
			sys.stdout.write('100.0%\n')
			print filename + ' download complete'
			return '111'

	def sync_recv_list(self,s, username): #receives files from client
		gene = s.recv(1024)
		print gene
		s.send('ok')
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
			s.sendall('ok')
			size = s.recv(16)
			size = int(size.strip())
			recvd = 0
			print filename + ' download in progress...'
			if not os.path.exists(downloadslocation):
				os.makedirs(downloadslocation)
			q = open(os.path.join(downloadslocation, filename), 'wb')
			while size > recvd:
				sys.stdout.write(str((float(recvd)/size)*100)[:4]+ '%' + '\r')
				sys.stdout.flush()
				data = s.recv(10240)
				if not data: 
					break
				recvd += len(data)
				q.write(data)
			s.sendall('ok')
			q.close()
			sys.stdout.write('100.0%\n')
			print filename + ' download complete'
			return '111'

	def receiveSpecFiles(self,s, username, list): # loops receiving files until master denies
		s.recv(2)
		s.sendall('ok')
		for file in list:
			s.recv(2)
			s.sendall('y')
			file = file.split('::')[0]
			s.recv(2)
			self.sync_recv_file(s, username, file)
		s.recv(2)
		s.sendall('n')

	def sendSpecFiles(self,s, username, list):
		s.recv(2)
		s.sendall('ok')
		for file in list:
			s.recv(2)
			s.sendall('y')
			file = file.split('::')[0]
			s.recv(2)
			self.sendItem(s, __location__ + ('/resources/programparts/sync/%s/' % username) + file)
		s.recv(2)
		s.sendall('n')


	def syncReceive(self,s, username):
		filelist = self.determineUnsyncedRecv(username)
		#return
		print 'starting to receive spec files'
		self.receiveSpecFiles(s, username, filelist)
		print 'done receiving spec files'
		clientfiles = []
		with open(__location__+'/resources/programparts/sync/%s/timestampclient.txt' % username, 'rb') as clienttimedoc:
			for line in clienttimedoc:
				clientfiles += [line]
		clientfiles = clientfiles[1:]
		#print clientfiles

		folder = __location__+'/resources/programparts/sync/%s/' % username
		if os.name == 'nt':
			folder = folder.replace('\\','/')

		filelist = []
		for file in clientfiles:
			#print file
			file = file.split('::')[0]
			file = folder + file
			filelist += [file]

		self.removeUnsyncedFiles(s, folder, filelist)

	def syncSend(self,s, username):
		filelist = self.determineUnsyncedSend(username)
		print 'starting to send spec files'
		self.sendSpecFiles(s, username, filelist)
		print 'done sending spec files'

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

	def timeCommand(self,s): # returns timestamp
		s.recv(4)
		now = datetime.utcnow()
		timestamp = now.strftime("%Y%m%d%H%M%S.%f")
		s.sendall(timestamp)
		print timestamp

	def isValidSize(self,s, username):
		size_dir = s.recv(64)

		conn = sqlite3.connect(__location__+'/resources/programparts/sync/syncdatabase.sqlite3')
		cur = conn.cursor()
		cur.execute('SELECT sizelim from Accounts WHERE username=?',(username,))
		size_lim = cur.fetchone()[0]

		if int(size_dir) <= int(size_lim):
			s.sendall('y')
			return (True,size_dir)
		else:
			s.sendall('n')
			return (False,None)

	def isAvailable(self,s, username):
		s.recv(1)

		conn = sqlite3.connect(__location__+'/resources/programparts/sync/syncdatabase.sqlite3')
		cur = conn.cursor()
		cur.execute('SELECT isAvailable from Accounts WHERE username=?',(username,))
		available = cur.fetchone()[0]
		print available

		if available != 0: #good to perform syncing
			s.sendall('y')
			return True
		else:
			s.sendall('n')
			return False

	def changeAvailable(self, username, newstatus):
		if newstatus:
			intBool = 1
		else:
			intBool = 0

		conn = sqlite3.connect(__location__+'/resources/programparts/sync/syncdatabase.sqlite3')
		cur = conn.cursor()
		cur.execute('UPDATE Accounts SET isAvailable=? WHERE username=?',(intBool,username))
		conn.commit()
		#all done

	def changeUserTimestamp(self, username, timestamp):
		conn = sqlite3.connect(__location__+'/resources/programparts/sync/syncdatabase.sqlite3')
		cur = conn.cursor()
		cur.execute('UPDATE Accounts SET synctimestamp=? WHERE username=?',(timestamp,username))
		conn.commit()

	def getUserTimestamp(self, username):
		conn = sqlite3.connect(__location__+'/resources/programparts/sync/syncdatabase.sqlite3')
		cur = conn.cursor()
		cur.execute('SELECT synctimestamp from Accounts WHERE username=?',(username,))
		synctimestamp = cur.fetchone()[0]
		return synctimestamp

	def syncCommand(self,s):
		item = self.checkAuthCommand(s)
		if not item[0]:
			print "authentication error"
			return "authentication error"
		username = item[1]
		passwordRaw = item[2]

		available = self.isAvailable(s, username)
		if not available:
			s.recv(2)
			response = "files currently in use"
			s.sendall(response)
			print "files currently in use"
			return "files currently in use"
		s.recv(2)

		self.changeAvailable(username, False) #change user data availability to False (0)
		newtimestamp = self.getUserTimestamp(username)
		syncLocList = self.getSyncLocations(username).split('|')[1:-1]

		try: #to prevent user's account from being locked forever

			self.sync_recv_list(s, username)

			valid,dirSize = self.isValidSize(s, username)
			if not valid:
				s.recv(2)
				response = "size too large"
				s.send(response)
				print "size too large"
				return "size too large"
			s.recv(2)

			with open(__location__+'/resources/programparts/sync/%s/timestampclient.txt' % username, 'r') as timeclient:
				clienttimestamp = timeclient.readline().strip()

			if not os.path.exists(__location__+'/resources/programparts/sync/%s/timestamp.txt' % username):
				with open(__location__+'/resources/programparts/sync/%s/timestamp.txt' % username, "a") as timedoc:
					timedoc.write("""00000000000000""")
			with open(__location__+'/resources/programparts/sync/%s/timestamp.txt' % username, "rb") as timedoc:
				servertimestamp = timedoc.readline().strip()
			print clienttimestamp
			print servertimestamp
			try:
				clienttimestamp = float(clienttimestamp)
				servertimestamp = float(servertimestamp)
				s.sendall('ok')
			except Exception,e:
				print str(e)
				s.sendall('no')
				s.recv(2)
				s.sendall('timestamp error')
				return 'timestamp error'
			s.recv(2)

			if servertimestamp < clienttimestamp:
				s.sendall('send')
				self.syncReceive(s, username)	
				if os.path.exists(__location__+'/resources/programparts/sync/%s/timestampclient.txt' % username):
					os.remove(__location__+'/resources/programparts/sync/%s/timestampclient.txt' % username)
				newtimestamp = clienttimestamp

				syncClient = self.loadClientClass('sync')
				syncClient.username = username
				syncClient.password = passwordRaw
				if syncClient != None:
					for syncLoc in syncLocList:
						try:
							if syncLoc != 'HERE':
								syncClient.should_encrypt = True
								if (syncLoc.startswith('192.168')):
									syncClient.should_encrypt = False
								syncClient.connectip(syncLoc,'spec' + dirSize,'sync')
						except Exception,e:
							print str(e)
				else:
					pass
				#receiveAllFiles(s, username)
			elif servertimestamp > clienttimestamp:
				s.sendall('recv')
				self.syncSend(s, username)
				if os.path.exists(__location__+'/resources/programparts/sync/%s/timestampclient.txt' % username):
					os.remove(__location__+'/resources/programparts/sync/%s/timestampclient.txt' % username)
				newtimestamp = servertimestamp
			elif servertimestamp == clienttimestamp:
				s.sendall('same')
				print 'client and server already synced'
				if os.path.exists(__location__+'/resources/programparts/sync/%s/timestampclient.txt' % username):
					os.remove(__location__+'/resources/programparts/sync/%s/timestampclient.txt' % username)
				return 'already synced'

		except Exception,e:
			print str(e)


		finally: #always set availability to true, always set synctimestamp to most recent timestamp, remove files if not supposed to be stored here
			self.changeAvailable(username, True)
			self.changeUserTimestamp(username, newtimestamp)
			if 'HERE' not in syncLocList:
				timestampLoc = __location__+'/resources/programparts/sync/%s/timestamp.txt' % username
				self.removeUnsyncedFiles(self,s, folder, [timestampLoc])
	#syncing is now complete


	def determineUnsyncedRecv(self,username):
		clientfiles = set()
		serverfiles = set()
		todownload = set()
		with open(__location__+'/resources/programparts/sync/%s/timestamp.txt' % username, 'rb') as servertimedoc:
			servertimedoc.readline()
			for line in servertimedoc:
				serverfiles.add(line.strip())
		with open(__location__+'/resources/programparts/sync/%s/timestampclient.txt' % username, 'rb') as clienttimedoc:
			clienttimedoc.readline()
			for line in clienttimedoc:
				clientfiles.add(line.strip())
		
		todownload = list(clientfiles - serverfiles)

		return todownload

	def determineUnsyncedSend(self,username):
		clientfiles = set()
		serverfiles = set()
		tosend = set()
		with open(__location__+'/resources/programparts/sync/%s/timestamp.txt' % username, 'rb') as servertimedoc:
			servertimedoc.readline()
			for line in servertimedoc:
				serverfiles.add(line.strip())
		with open(__location__+'/resources/programparts/sync/%s/timestampclient.txt' % username, 'rb') as clienttimedoc:
			clienttimedoc.readline()
			for line in clienttimedoc:
				clientfiles.add(line.strip())
		
		tosend = list(serverfiles - clientfiles)

		return tosend

	def sendItem(self,s,data): #send file to seed

		print 'sending data'								   
		s.sendall(data)
		print 'awaiting reply'
		s.recv(2)

		#file_name,destination = data.split("@@")
		file = data

		file_name = data.split('/')[-1]

		#print os.path.join(uploads, file_name)
		print file
		if os.path.exists(file):
			print file_name + " found"
			s.sendall('ok')
			#s.recv(2)
			#s.sendall('%16d' % self.send_cache)

			if s.getKey() == None:
				use_cache = self.send_cache
			else:
				use_cache = self.send_cache_enc
			#file_cache = s.recv(16)
			s.sendall('%16d' % use_cache)

			s.recv(2)

			filelength =  os.path.getsize(file)
			#s.sendall('%16d' % filelength)
			s.sendall('%16d' % filelength)
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
					s.sendall(data)
			s.recv(2)
			sys.stdout.write('100.0%   ' + str(sent) + '/' + str(filelength) + ' B\n')
			print file_name + " sending successful"
			
		else:
			print file_name + " not found"
			s.sendall('no')

	def newUserCommand(self,s):
		improperChar = '|' # list of improper characters
		username = s.recv(32).lower()
		proper = True
		error = 'empty error string'
		for item in improperChar:
			if item in username:
				proper = False
				error = 'improper characters used'

		conn = sqlite3.connect(__location__+'/resources/programparts/sync/syncdatabase.sqlite3')
		cur = conn.cursor()
		cur.execute('SELECT username from Accounts WHERE username=?',(username,))
		exists = cur.fetchone()

		if exists != None:
			proper = False
			error = 'username already exists'

		if not proper:
			s.sendall('n')
			print error
			s.recv(2)
			s.sendall(error)
			return
		else:
			s.sendall('y')
			salt = ''
			for n in range(0,self.saltlength):
				salt += self.char[random.randrange(0,len(self.char))]
			try:
				passwordRaw = s.recv(128)
				passwordHash = sha1(salt + passwordRaw).hexdigest()
				s.sendall('y')
			except Exception,e:
				print str(e)
				s.sendall('n')
				s.recv(2)
				s.sendall(e)
				return

			accountSizeLim = 1280000000 # 1.28 GB
			synclocations = self.selectSyncLocations(accountSizeLim)
			newtimestamp = 0

			#check if valid token has been submitted
			s.recv(2)
			if self.requireToken:
				s.sendall('rt')
				requested_token = s.recv(128)
				tokenClient = self.loadClientClass('token')
				tokenServerIP = self.getTokenServer()
				if tokenServerIP == None:
					s.sendall('n')
					s.recv(2)
					s.sendall('bad server configuration')
					print 'ERROR: server was not given any token servers!'
					return
				validToken = tokenClient.connectip(tokenServerIP,requested_token+'|'+self.varDict["name"],'checkout')
				if validToken:
					s.sendall('y')
				else:
					s.sendall('n')
					s.recv(2)
					s.sendall('client provided bad token')
					print 'client provided bad token'
					return
			else:
				s.sendall('ok')


			cur.execute('INSERT INTO Accounts (salt, username, password, sizelim, isAvailable, locations, synctimestamp) VALUES (?,?,?,?,?,?,?)', (salt,username,passwordHash,accountSizeLim,1,synclocations,newtimestamp))
			conn.commit()
			print 'User %s added.' % username
			self.createUserDir(username)
		cur.close()

		syncLocList = self.getSyncLocations(username)
		syncLocList = syncLocList.split('|')[1:-1]
		
		syncClient = self.loadClientClass('sync')
		syncClient.username = username
		syncClient.password = passwordRaw
		if syncClient != None:
			for syncLoc in syncLocList:
				try:
					if syncLoc != 'HERE':
						syncClient.connectip(syncLoc,'createAccount','newuser')
				except Exception,e:
					print str(e)
		else:
			pass

	def getTokenServer(self):
		with open(__location__+'/resources/programparts/sync/tokenservers.txt', "r") as seeds:
			for line in seeds:
				if line.startswith('||'):
					#try: #connect to ip, save data, issue command
					return line.split("||")[1]
			return None

	def selectSyncLocations(self,sizelim):
		synclocations = None
		with open(__location__+'/resources/programparts/sync/synclocations.txt', 'r') as locations:
			for line in locations:
				line = line.strip()
				if line.startswith('|') and line.endswith('|'):
					try:
						synclocations = line
					except Exception,e:
						print str(e)
					break
		if synclocations == None:
			return '|HERE|'
		else: #for now use all that are there
			return '|HERE' + synclocations
			
	def getSyncLocations(self, username):
		conn = sqlite3.connect(__location__+'/resources/programparts/sync/syncdatabase.sqlite3')
		cur = conn.cursor()
		cur.execute('SELECT locations from Accounts WHERE username=?',(username,))
		synclocations = cur.fetchone()[0]
		return synclocations

	def createUserDir(self,username):
		if not os.path.exists(__location__+'/resources/programparts/sync/%s' % username):
			os.makedirs(__location__+'/resources/programparts/sync/%s' % username)
			with open(__location__+'/resources/programparts/sync/%s/timestamp.txt' % username, "a") as timedoc:
				timedoc.write("""00000000000000""")

	def checkAuthCommand(self,s):
		username = s.recv(32).lower()
		info = self.isUser(username)
		if not info[0]:
			s.sendall('n')
			print "username does not exist"
			return (False,None,None)
		s.sendall('y')
		#passwordHash = sha1(info[1] + s.recv(128)).hexdigest()
		passwordRaw = s.recv(128)
		passwordHash = sha1(info[1] + passwordRaw).hexdigest()
		match = self.passwordMatch(username,passwordHash)
		if match:
			s.sendall('y')
			print "username/password match"
			return (True,username,passwordRaw)
		else:
			s.sendall('n')
			print "username/password do not match"
			return (False,None,None)


	def isUser(self,username): #check is username exists
		username = username.lower()
		exists = False
		salt = None

		conn = sqlite3.connect(__location__+'/resources/programparts/sync/syncdatabase.sqlite3')
		cur = conn.cursor()
		cur.execute('SELECT salt from Accounts WHERE username=?',(username,))
		data = cur.fetchone()
		if data != None:
			exists = True
			salt = data[0]

		return (exists,salt)

	def passwordMatch(self,username,passwordHash): #check if password is a match
		match = False
		conn = sqlite3.connect(__location__+'/resources/programparts/sync/syncdatabase.sqlite3')
		cur = conn.cursor()
		cur.execute('SELECT password from Accounts WHERE username=?',(username,))
		data = cur.fetchone()
		if data != None:
			passwordStored = data[0]
			if passwordHash == passwordStored:
				match = True

		#cur.execute('SELECT * from Accounts')
		#data = cur.fetchone()
		#for row in data:
		#	print row

		return match

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

	def sizeCommand(self,s):
		pass

	def exit(self): #kill all proceses for a tidy exit
		self.shouldExit = True

if __name__ == '__main__':
	CommonCode_Server.main(sys.argv[1:],TemplateServer)