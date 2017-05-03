import sys, socket, select, os, threading, getopt, multiprocessing, subprocess
from time import strftime, sleep, time
from datetime import datetime
from hashlib import sha1

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

class TemplateServer(CommonCode_Server.TemplateServer):

	# don't change this
	netPass = None
	key = None
	pubkey = None
	threads = []
	pipes = []
	startTime = None
	# change this to default values
	version = '3.0.0'
	serverport = 9016
	useConfigPort = True
	scriptname = 'master'
	function = 'master_function'
	name = 'seed'
	downloadAddrLoc = 'jedkos.com:9011&&protocols/master.py' 
	#form is ip:port&&location/on/filetransferserver/file.py

	def __init__(self, serve=None):
		CommonCode_Server.TemplateServer.__init__(self,serve)
		self.seedLock = multiprocessing.Lock()
		self.seedDict = {}
		self.processID = 0

	def run_processes(self):
		try:
			self.servergen(self,self.removeBrokenProcesses)
		except Exception,e:
			print str(e)
			self.shouldExit = True

	def init_spec(self):
		self.funcMap = {
		'receive':self.receiveCommand,
		'runproc':self.runProcSeed,
		'viewproc':self.viewProcSeed,
		'stopproc':self.stopProcSeed,
		'closeseed':self.closeSeed,
		'send':self.sendCommand
		}
		# insert application-specific initialization code here
		if not os.path.exists(__location__+'/resources/programparts/%s' % self.name): os.makedirs(__location__+'/resources/programparts/%s' % self.name)

	def loadClientClass(self,data): #used to start protocols not requiring connection
		
		try:
			scriptname = data[0]
			compat = 'n'
			with open(__location__+'/resources/protocols/protlist.txt') as protlist:
				for line in protlist:
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
						return 'protocol is not specified as standalone'
				varcheck = getattr(script,'variables')
				if len(varcheck) <= len(data):
					function = getattr(script,'serverfunction')
					use = getattr(script,function)
					print 'success'
				else:
					print 'incorrect argument[s]'
			else:
				return 'failure - protocol not found'

			clientClass = use(__location__)
			print type(clientClass)
			return clientClass
		except Exception,e:
			print str(e)
			return None

	def loadClientFunction(self,data): #used to start protocols not containing a class

		try:
			scriptname = data[0]
			compat = 'n'
			with open(__location__+'/resources/protocols/protlist.txt') as protlist:
				for line in protlist:
					if line == scriptname or line == scriptname + '\n' :
						compat = 'y'
						break

			if compat == 'y':
				script = sys.modules[scriptname]
				try:
					isAlone = getattr(script,'standalone')
				except:
					isAlone = True
				finally:
					if isAlone:
						return 'protocol is not specified as standalone'
				varcheck = getattr(script,'variables')
				if len(varcheck) <= len(data):
					function = getattr(script,'clientfunction')
					use = getattr(script,function)
					print 'success'
				else:
					print 'incorrect argument[s]'
			else:
				return 'failure - protocol not found'

			clientFunc = use
			print type(clientFunc)
			return clientFunc
		except Exception,e:
			print str(e)
			return None

	def serverterminal(self,inp): #used for server commands
		if inp:
			if inp == 'exit':
				self.exit()
			elif inp == 'clear':
				self.clear()
			elif inp == 'info':
				self.info()

	def seed_recv_file(self,s): #receives files from master
		gene = s.recv(1024)

		s.send('ok')
		downloadslocation,filename = gene.split(':')

		downloadslocation = __location__ + downloadslocation 

		has = s.recv(2)
		if has != 'ok':
			return '404'
		else:
			s.sendall('ok')
			file_cache = s.recv(16)
			file_cache = int(file_cache.strip())
			s.sendall('ok')
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
				data = s.recv(file_cache)
				if not data: 
					break
				recvd += len(data)
				q.write(data)
			s.sendall('ok')
			q.close()
			sys.stdout.write('100.0%   ' + str(recvd) + '/' + str(size) + ' B\n')
			print filename + ' download complete'
			return '111'

	def receiveCommand(self,s):
		while True:
			sending = s.recv(1)
			s.sendall('ok')
			if sending == 'y':
				self.seed_recv_file(s)
			else:
				break
		print "receive files complete"

	def seed_send_folder(self,s,folder,dest):
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
				self.seed_send_file(s,itempath,dest)
			elif os.path.isdir(itempath):
				newloc = itempath.split(loc)[1]
				destnew = dest+newloc+'/'
				syncedfiles += self.seed_send_folder(s,itempath,destnew)
		return syncedfiles

	def seed_send_file(self,s,loc,dest):
		file = loc
		file_name = loc.split('/')[-1]

		s.sendall(dest+':'+file_name)

		file_cache = s.recv(16)
		file_cache = int(file_cache.strip())
		
		filelength = os.path.getsize(file)
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
				data = f.read(file_cache)
				s.sendall(data)
				if not data:
					break
				sent += len(data)

		s.recv(2)
		sys.stdout.write('100.0%   ' + str(sent) + '/' + str(filelength) + ' B\n')
		print file_name + " sending successful"

	def processGeneSeed(self,s):
		gene = s.recv(1024)
		loc = __location__ + gene
		if os.path.isdir(loc):
			s.sendall('dd')
			s.recv(2)
			self.seed_send_folder(s,loc,'/')
			s.sendall('n')

		elif os.path.isfile(loc):
			s.sendall('ff')
			s.recv(2)
			self.seed_send_file(s,loc,'/')
			s.sendall('ok')
		else: # is not recognized, so skip
			s.sendall('nn')


	def sendCommand(self,s):
		#FILL OUT
		while True:
			sending = s.recv(1)
			if sending == 'y':
				self.processGeneSeed(s)
			else:
				break
		print "send files complete"


	def attemptRunThread(self,fileloc,inp):
		filename = fileloc.split('/')[-1]
		print 'attempting to start ' + filename
		print fileloc
		fileloc = __location__+fileloc

		print fileloc
		#parent,child = multiprocessing.Pipe()
		#parent_sub = subprocess.PIPE
		#child_sub = subprocess.PIPE
		if filename.endswith('.py'):
			filename_clean = filename[:-3]
		else:
			filename_clean = filename
		processname = filename_clean + str(self.processID)
		conn_port = None
		try:
			directory,module_name = os.path.split(fileloc)
			print "%s,%s" % (directory,module_name)
			module_name = os.path.splitext(module_name)[0]

			path = list(sys.path)
			sys.path.insert(0,directory)
			try:
				module = __import__(module_name) #cool import command
			finally:
				sys.path[:] = path
			if inp == '':
				process = subprocess.Popen(['python',fileloc,'-t'])
				conn_port = module.TemplateServer.serverport
			else:
				try:
					conn_port = int(inp)
				except Exception,e:
					raise ValueError('port must be an integer')
				process = subprocess.Popen(['python',fileloc,'-p',inp,'-t'])
			#attempt to start socket for admin comms
			process_conn = ("localhost",conn_port+1000)
			
		except Exception,e:
			print "failure running " + processname + " : " + str(e)
			return (False,str(e))
		else:
			print 'thread started, working after'
			self.seedLock.acquire()
			creationDate = datetime.utcnow()
			creation = creationDate.strftime("%Y%m%d%H%M%S")
			self.seedDict.setdefault(processname,(process,process_conn,creation))#,processthread))
			self.processID += 1
			self.seedLock.release()
		print "Process Dictionary: " + str(self.seedDict)
		print processname  + ' started'
		return (True,None)


	def runProcSeed(self,s): # loops receiving files until master denies
		while True:
			sending = s.recv(1)
			s.sendall('ok')
			if sending  == 'y':
				filetorun = s.recv(1024)
				fileloc,inp = filetorun.split('@@')
				print inp
				success,error = self.attemptRunThread(fileloc,inp)
				if success:
					s.sendall('y')
				if not success:
					s.sendall('n')
					s.recv(2)
					s.sendall(error)
			else:
				break

	def viewProcSeed(self,s):
		s.recv(2)
		for operation in self.seedDict:
			s.sendall('y')
			s.recv(2)
			s.sendall(operation)
			s.recv(2)
		s.sendall('n')
		print 'operations sent'

	def attemptStopThread(self,procname):
		print "Process Dictionary: " + str(self.seedDict)
		try:
			self.seedLock.acquire()
			procObj = self.seedDict.pop(procname,None)
			if procObj == None:
				return (False,'process name does not exist')
			conn_info = procObj[1]
			try:
				s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				s.connect((conn_info[0],conn_info[1]))
			except Exception,e:
				pass
			else:
				s.sendall("exit")
		except Exception,e:
			return (False,str(e))
		finally:
			self.seedLock.release()
		print "Process Dictionary: " + str(self.seedDict)
		return (True,None)

	def stopProcSeed(self,s):
		while True:
			sending = s.recv(1)
			s.sendall('ok')
			if sending  == 'y':
				proctostop = s.recv(1024)
				success,error = self.attemptStopThread(proctostop)

				if success:
					s.sendall('y')
				if not success:
					s.sendall('n')
					s.recv(2)
					s.sendall(error)
			else:
				break

	def closeSeed(self, s):
		s.close();
		self.exit();

	def removeBrokenProcesses(self):
		#multiprocessing.active_children()
		keys_to_pop = []
		currentDate = datetime.utcnow()
		current = currentDate.strftime("%Y%m%d%H%M%S")
		for procseed,data in self.seedDict.iteritems():
			if int(current) - int(data[2]) < 7:
				continue 
			removeProc = False
			conn_info = data[1]
			try:
				s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				s.connect((conn_info[0],conn_info[1]))
			except Exception,e:
				print "Exception for %s: %s" % (procseed,str(e))
				removeProc = True
			else:
				s.sendall("")
			if removeProc:
				keys_to_pop.append(procseed)
		for key in keys_to_pop:
			#remove process
			print 'removing %s' % key
			self.seedLock.acquire()
			try:
				self.seedDict.pop(key)
			except:
				pass
			finally:
				self.seedLock.release()

	def cleanProcesses(self):
		for name in self.seedDict.keys():
			try:
				self.attemptStopThread(name)
			except Exception,e:
				print "ERROR at %s: %s" % (name,str(e))
			else:
				print '%s closed!' % name

	def exit(self): #kill all processes for a tidy exit
		self.shouldExit = True
		self.cleanProcesses()

if __name__ == '__main__':
	CommonCode_Server.main(sys.argv[1:],TemplateServer)