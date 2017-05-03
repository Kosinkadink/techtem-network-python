#!/usr/bin/python2
import sys, socket, select, os, threading, sqlite3
from time import strftime, sleep, time
from hashlib import sha1, md5
from getpass import getpass

common_location = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__))) #directory from which this script is ran
main_dir = os.path.realpath(os.path.join(common_location,'..'))
sys.path.insert(0, os.path.join(main_dir,'source/'))
import CommonCode
import CommonCode_Client
	
#universal variables
variables = []
standalone = True
version = '3.0.0'
standalonefunction = 'standalone_function'
__location__ = None
clientfunction = None
serverfunction = 'server_function'
#script-specific variables

class TemplateProt(CommonCode_Client.TemplateProt):

	scriptname = 'master'
	scriptfunction = 'master_function'
	version = '3.0.0'

	def __init__(self,location,startTerminal):
		global __location__
		__location__ = location
		CommonCode_Client.TemplateProt.__init__(self,location,startTerminal)

	def init_spec(self):
		self.funcMap = {
			'receive':self.sendCommand,
			'send':self.receiveCommand,
			'runproc':self.runProcMaster,
			'viewproc':self.viewProcMaster,
			'stopproc':self.stopProcMaster,
			'diagnostics':self.diagnosticsCommand
		}
		#master files start
		if not os.path.exists(__location__+'/resources/programparts/master'): os.makedirs(__location__+'/resources/programparts/master')

		if not os.path.exists(__location__+'/resources/programparts/master/seedsend.txt'):
			with open(__location__+'/resources/programparts/master/seedsend.txt', "a") as seeds:
				seeds.write("""#################################################################
##The format for files is: ||ip:port||/directory/filetosend.extension@@/destinationfolder/||
##The format for files is: ||ip:port||/directory/of/folder@@/destination/for/all/files/in/folder/||
##Destination is relative to the location of the seed script. To place in resources folder, /resources/
##If destination is same directory as location of the seed script, destination is: /
##Only line starting with || will be read. Any line not starting with || will not be read.
#################################################################
""")

		if not os.path.exists(__location__+'/resources/programparts/master/seedrecv.txt'):
			with open(__location__+'/resources/programparts/master/seedrecv.txt', "a") as seeds:
				seeds.write("""#################################################################
##The format for files is: ||ip:port||/directory/filetosend.extension@@/destinationfolder/||
##The format for files is: ||ip:port||/directory/of/folder@@/destination/for/all/files/in/folder/||
##Destination is relative to the location of the client script. To place in resources folder, /resources/
##If destination is same directory as location of the client script, destination is: /
##Only line starting with || will be read. Any line not starting with || will not be read.
#################################################################
""")

		if not os.path.exists(__location__+'/resources/programparts/master/seedrun.txt'):
			with open(__location__+'/resources/programparts/master/seedrun.txt', "a") as seeds:
				seeds.write("""####################################################
##The format is: ||ip:port||/directory/of/filetorun.txt@@input||
##If no input, NOINPUT
##Destination is relative to the location of the seed script. To run script in resources folder, /resources/
##If destination is same directory as location of the seed script, destination is: /
##Only line starting with || will be read. Any line not starting with || will not be read.
####################################################
""")
		#master files end

	def boot(self):
		self.clear()
		print "TechTem Network Master started"
		print "Version " + self.version
		if self.shouldEncrypt:
			print "Encryption is ON"
		else:
			print "Encryption is OFF"
		print "Type help for command list\n"

	def help(self):
		print "\nping + (address): check if seed at address is online"
		print "pingall + (file.txt): check if all seeds in file are online"
		print "sendall + (file.txt): send all files to all seeds according to specified file"
		print "send + (seed ip) + (file.txt): send all files to seed in specified file"
		print "recvall + (file.txt): recv all files from all seeds according to specified file"
		print "runall + (file.txt): start all files to all seeds according to specified file"
		print "run + (seed ip) + (file.txt): send all files to seed in specified file"
		print "stop + (seed ip:port) + (procname): stop the process with specified name on seed"
		print "list + (file.txt): print all seeds in file"
		print "procall + (file.txt): returns all the running processes on seed"
		print "encrypt OR enc: toggle encryption status"
		print "clear: clears screen"

	#function for client splash screen
	def serverterminal(self):
		self.boot()
		while 1:
			inp = raw_input(">")
			try:
				if inp:
					# PING ALL SEEDS
					if inp.split()[0] == 'pingall':
						try:
							filedir = inp.split()[1]
						except:
							filedir = "seedsend.txt" 
						self.pingall(filedir)
					# PING CHOSEN SEED
					elif inp.split()[0] == 'ping':
						try:
							ip = inp.split()[1]
						except:
							ip = None 
						print self.ping(ip)+'\n'
					# TOGGLE ENCRYPTION
					elif inp.split()[0] in ['encrypt','enc']:
						self.shouldEncrypt = self.toggleEncrypt(self.shouldEncrypt)
					# SEND TO ALL SEEDS IN CHOSEN FILE
					elif inp.split()[0] == 'sendall':
						try:
							filedir = inp.split()[1]
						except:
							filedir = "seedsend.txt"
						start = time()
						try:
							self.sendtoall(filedir)
						except IOError:
							print "Error: seed file not found"
						end = time()
						print "Command (sendall) time: %s" % str(end-start)
					# RECEIVE FROM ALL SEEDS IN CHOSEN FILE
					elif inp.split()[0] == 'recvall':
						try:
							filedir = inp.split()[1]
						except:
							filedir = "seedrecv.txt"
						start = time()
						try:
							self.recvfromall(filedir)
						except IOERROR:
							print "Error: seed file not found"
						end = time()
						print "Command (recvall) time: %s" % str(end-start)
					# RUN SCRIPTS ON ALL SEEDS IN CHOSEN FILE
					elif inp.split()[0] == 'runall':
						try:
							filedir = inp.split()[1]
						except:
							filedir = "seedrun.txt"
						self.runall(filedir)
					# QUIT MASTER
					elif inp.split()[0] == 'quit' or inp.split()[0] == 'leave' or inp.split()[0] == 'exit':
						break
					# LIST ALL SEEDS IN CHOSEN FILE
					elif inp.split()[0] == 'list':
						try:
							filedir = inp.split()[1]
						except:
							filedir = "seedsend.txt"
						self.seedList(filedir)
					# LIST ALL RUNNING PROCESSES IN SEEDS IN CHOSEN FILE
					elif inp.split()[0] == 'procall':
						try:
							filedir = inp.split()[1]
						except:
							filedir = "seedsend.txt"
						self.procSeedAll(filedir)
					# STOP A PROCESS ON A CHOSEN SEED
					elif inp.split()[0] == 'stop':
						try:
							seedip = inp.split()[1]
						except:
							seedip = None
						try:
							proctostop = [inp.split()[2]]
						except:
							proctostop = None
						self.connectip(self,seedip,proctostop,'stopproc')
					# CLOSE ALL SEEDS IN CHOSEN FILE
					elif inp.split()[0] == 'closeall':
						try:
							filedir = inp.split()[1]
						except:
							filedir = "seedsend.txt"
						self.closeAll(filedir)
					# CLOSE A CHOSEN SEED
					elif inp.split()[0] == 'close':
						try:
							ip = inp.split()[1]
						except:
							print("Error: no seed IP provided\n")
						else:
							self.closeOne(ip)
					# CLEAR SCREEN
					elif inp.split()[0] == 'clear':
						self.boot()
					# SHOW INFO
					elif inp.split()[0] == 'info':
						self.info_script()
					# SHOW COMMANDS
					elif inp.split()[0] == 'help' or inp.split()[0] == '?':
						self.help()
					else:
						print "Invalid command"
			except Exception,e:
				print str(e)


	def info_script(self):
		print "Send Cache (Normal): %s" % self.send_cache
		print "Send Cache (Encrypted): %s" % self.send_cache_enc
		print "AES Key Length (bytes): %s" % self.AES_keysize
		print "Encryption Activated: %s" % self.shouldEncrypt
		print ""

	def closeAll(self,filedir):
		with open(__location__+'/resources/programparts/master/'+filedir, "r") as seeds:
			for line in seeds:
				if line.startswith('||'):
					self.closeOne(line.split("||")[1])

	def closeOne(self,ip):
		try:
			print self.connectip(self,ip,'closeseed','closeseed')
		except:
			print "line is poorly formatted"

	def seedList(self,filedir):
		with open(__location__+'/resources/programparts/master/'+filedir, "r") as seedlist:
			for line in seedlist:
				if line.startswith('||'):
					try:
						print line.split('||')[1]
					except Exception,e:
						print str(e)

	def procSeedAll(self,filedir):
		with open(__location__+'/resources/programparts/master/'+filedir, "r") as seeds:
			for line in seeds:
				if line.startswith('||'):
					try:
						print self.connectip(self,line.split("||")[1],'viewproc','viewproc')
					except:
						print "line is poorly formatted"
		print ''		

	def pingallrepeat(self,filedir): #ping all seeds every set period of time
		while 1:
			self.pingall(filedir)
			sleep(10)

	def pingall(self,filedir): #ping all seeds on list to determine what seeds are online
		with open(__location__+'/resources/programparts/master/'+filedir, "r") as seeds:
			for line in seeds:
				if line.startswith('||'):
					try:
						print self.ping(line.split("||")[1])
					except:
						print "line is poorly formatted"
		print ''

	def ping(self,ip): #attempt to connect to ip to determine if server is online
		try:
			host = ip.split(':')[0]
			port = int(ip.split(':')[1])
		except:
			return 'invalid host/port provided'
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.settimeout(2)
		try:
			s.connect((host, port))
		except:
			s.close
			return ip + " seed NOT online"
		s.close
		return ip + " seed online"

	def sendtoall(self,filedir): #initialize all seeds by sending/starting files
		with open(__location__+'/resources/programparts/master/'+filedir, "r") as seeds:
			for line in seeds:
				if line.startswith('||'):
					try: #connect to ip, save data, issue command
						print self.connectip(self,line.split("||")[1],line.split("||")[2:-1],'receive')
					except Exception,e:
						print str(e) + "\n"
		print ''

	def recvfromall(self,filedir): #get files/folders from seeds
		with open(__location__+'/resources/programparts/master/'+filedir, "r") as seeds:
			for line in seeds:
				if line.startswith('||'):
					try: #connect to ip, save data, issue command
						print self.connectip(self,line.split("||")[1],line.split("||")[2:-1],'send')
					except Exception,e:
						print str(e) + "\n"
		print ''

	def runall(self,filedir):
		with open(__location__+'/resources/programparts/master/'+filedir, "r") as seeds:
			for line in seeds:
				if line.startswith('||'):
					try: #connect to ip, save data, issue command
						print self.connectip(self,line.split("||")[1],line.split("||")[2:-1],'runproc')
					except Exception,e:
						print str(e) + "\n"
		print ''

	def sendItem(self,s,loc,dest): #send file to seed

		print 'sending data'
		file_name = loc.split('/')[-1]
		to_send = dest+':'+file_name
		s.sendall(to_send)

		print 'awaiting reply'
		s.recv(2)

		file = loc

		if os.path.exists(file):
			print file_name + " found"
			s.sendall('ok')
			s.recv(2)
			use_cache = self.send_cache
			s.sendall('%16d' % use_cache)
			s.recv(2)

			filelength =  os.path.getsize(file)
			s.sendall('%16d' % filelength)
			with open(file, 'rb') as f:
				print file_name + " sending..."
				sent = 0
				while filelength > sent:
					try:
						sys.stdout.write(str((float(sent)/filelength)*100)[:4]+ '%   ' + str(sent) + '/' + str(filelength) + ' B\r')
						sys.stdout.flush()
					except:
						pass
					data = f.read(use_cache)
					s.sendall(data)
					if not data:
						break
					sent += len(data)

			s.recv(2)
			sys.stdout.write('100.0%   ' + str(sent) + '/' + str(filelength) + ' B\n')
			print file_name + " sending successful"
			
		else:
			print file_name + " not found"

	def sendFolder(self,s,folder,dest):
		syncedfiles = []
		loc = folder
		for item in os.listdir(folder):
			itempath = os.path.join(folder, item)
			if os.name == 'nt':
				itempath = itempath.replace('\\','/')
			if os.path.isfile(itempath):
				syncedfiles += [itempath]
				s.sendall('y')
				s.recv(2)
				self.sendItem(s,itempath,dest)
			elif os.path.isdir(itempath):
				newloc = itempath.split(loc)[1]
				destnew = dest+newloc+'/'
				syncedfiles += self.sendFolder(s,itempath,destnew)
		return syncedfiles

	def sendSeedFiles(self,s, folder, dest):
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
				loc = itempath.split(__location__)[1]
				self.sendItem(s,loc,dest)
			elif os.path.isdir(itempath):
				syncedfiles += self.sendSeedFiles(s, itempath, dest)
		return syncedfiles

	def diagnosticsCommand(self,ser, data): #request diagnostics from seed
		pass

	def sendCommand(self,s, data): #make seed receive all files from master
		for gene in data:
			loc,dest = gene.split('@@')
			loc = __location__ + loc
			if os.path.isdir(loc):
				self.sendFolder(s,loc,dest)
			elif os.path.isfile(loc):
				s.sendall('y')
				s.recv(2)
				self.sendItem(s,loc,dest)

		s.sendall('n')
		print 'sending query complete'


	def recvItem(self,s,dest):
		gene = s.recv(1024)
		destExtra,filename = gene.split(':')
		
		downloadslocation = dest + destExtra[1:]

		use_cache = self.send_cache

		s.sendall('%16d' % use_cache)

		size = s.recv(16)
		size = int(size.strip())
		recvd = 0
		print filename + ' download in progress...'
		if not os.path.exists(downloadslocation):
			os.makedirs(downloadslocation)
		q = open(os.path.join(downloadslocation, filename), 'wb')
		while size > recvd:
			sys.stdout.write(str((float(recvd)/size)*100)[:4]+ '%   ' + str(recvd) + '/' + str(size) + ' B\r')
			sys.stdout.flush()
			data = s.recv(use_cache)
			if not data: 
				break
			recvd += len(data)
			q.write(data)
		s.sendall('ok')
		q.close()
		sys.stdout.write('100.0%   ' + str(recvd) + '/' + str(size) + ' B\n')
		print filename + ' download complete'
		return '111'


	def receiveCommand(self,s,data):
		#FILL OUT
		for gene in data:
			loc,dest = gene.split('@@')
			dest = __location__ + dest
			s.sendall('y')
			# seed processes gene here
			s.sendall(loc)
			status = s.recv(2)
			if status == 'nn':
				print "%s does not exist on seed, skipping..." % loc
			elif status == 'ff':
				print "%s does exist; is file" % loc
				s.sendall('ok')
				self.recvItem(s,dest)
				s.recv(2)
			elif status == 'dd':
				print "%s does exist; is directory" % loc
				s.sendall('ok')
				while True:
					sending = s.recv(1)
					if sending != 'y':
						break
					else:
						s.sendall('ok')
						self.recvItem(s,dest)
			else:
				print 'status %s not understood, quitting...' % status
				return 'not successful'
				
		s.sendall('n')
		print 'receiving query complete'

	def runProcMaster(self,s,data):
		for gene in data:
			s.sendall('y')
			s.recv(2)
			s.sendall(gene)
			filename = gene.split('@@')[0].split('/')[-1]
			'seed attempting to run ' + filename
			success = s.recv(1)
			if success == 'y':
				print 'success running ' + filename
			else:
				s.sendall('ok')
				error = s.recv(1024)
				print 'failure running ' + filename + ' : ' + error

	def viewProcMaster(self,s,data):
		operations = []
		s.sendall('ok')
		while True:
			another = s.recv(1)
			if another == 'y':
				s.sendall('ok')
				operations += [s.recv(1024)]
				s.sendall('ok')
			else:
				break
		for operation in operations:
			print operation

	def stopProcMaster(self,s,data):
		for gene in data:
			s.sendall('y')
			s.recv(2)
			s.sendall(gene)
			procname = gene
			#filename = gene.split('@@')[0].split('/')[-1]
			'seed attempting to stop ' + procname
			success = s.recv(1)
			if success == 'y':
				print 'success stopping ' + procname
			else:
				s.sendall('ok')
				error = s.recv(1024)
				print 'failure stopping ' + procname + ' : ' + error
		s.sendall('n')
		s.recv(2)

	def master_broadcast(self,command):
		pass

	def exit(self):
		quit()

def standalone_function(data,location,startTerminal):
	TemplateProt(location,startTerminal)
	return "Left master client, back in main client"

def server_function(location):
	return TemplateProt(location,False)

if __name__ == "__main__":
	location = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__))) #directory from which this script is ran
	if os.name == 'nt':
		location = location.replace('\\','/')
	TemplateProt(location,True)