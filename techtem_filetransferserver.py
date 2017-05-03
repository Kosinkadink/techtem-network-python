import sys, socket, select, os, threading, getopt
from time import strftime, sleep

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
	startTime = None
	# change this to default values
	version = '3.0.0'
	serverport = 9011
	send_cache = 40960
	send_cache_enc = 40960
	RSA_bitlength = 2048
	shouldEncrypt = True
	shouldEncryptDownload = True
	scriptname = 'filetransfer'
	function = 'filetransfer_client'
	name = 'filetransfer'
	downloadAddrLoc = 'jedkos.com:9011&&protocols/filetransfer.py' 
	#form is ip:port&&location/on/filetransferserver/file.py

	def __init__(self, serve=serverport):
		CommonCode_Server.TemplateServer.__init__(self,serve)

	def init_spec(self):
		self.funcMap = {'fileget':self.fileSendCommand}
		# insert application-specific initialization code here
		if not os.path.exists(__location__+'/resources/programparts/filetransfer'): os.makedirs(__location__+'/resources/programparts/filetransfer')
		if not os.path.exists(__location__+'/resources/programparts/filetransfer/approvedfiles.txt'):
			with open(__location__+'/resources/programparts/filetransfer/approvedfiles.txt', "a") as makeprot:
				makeprot.write("")

	def serverterminal(self,inp): #used for server commands
		if inp:
			if inp == 'exit':
				self.exit()
			elif inp == 'clear':
				self.clear()
			elif inp == 'info':
				self.info()

	def sendFile(self,s): #send file to seed

		fileloc = s.recv(1024)
		print 'searching for %s' % fileloc
		searchfile = __location__ + '/resources/uploads/' + fileloc

		try:
			file_name = fileloc.split('/')[-1]
		except:
			file_name = fileloc

		file = searchfile

		if os.path.exists(file):
			print file_name + " found"
			s.sendall('ok')
			s.recv(2)

			if s.getKey() == None:
				use_cache = self.send_cache
			else:
				use_cache = self.send_cache_enc

			s.sendall('%16d' % use_cache)
			s.recv(2)

			filelength =  os.path.getsize(file)
			s.sendall('%16d' % filelength)
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

	def fileSendCommand(self,s):
		self.sendFile(s)

	def exit(self): #kill all proceses for a tidy exit
		self.shouldExit = True

if __name__ == '__main__':
	CommonCode_Server.main(sys.argv[1:],TemplateServer)