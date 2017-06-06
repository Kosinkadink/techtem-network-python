import sys, socket, select, os, threading, getopt, multiprocessing
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
	pipes = []
	startTime = None
	# change this to default values
	version = '3.0.0'
	serverport = 9999
	useConfigPort = True
	send_cache = 40960
	send_cache_enc = 40960
	RSA_bitlength = 2048
	shouldEncrypt = True
	shouldEncryptDownload = True
	scriptname = None
	function = None
	name = 'template'
	downloadAddrLoc = 'jedkos.com:9011&&protocols/name.py' 
	#form is ip:port&&location/on/filetransferserver/file.py

	def __init__(self, serve=serverport):
		CommonCode_Server.TemplateServer.__init__(self,serve)

	def init_spec(self):
		self.funcMap = {} # fill in with a string key and a function value
		# insert application-specific initialization code here
		if not os.path.exists(__location__+'/resources/programparts/%s' % self.name): os.makedirs(__location__+'/resources/programparts/%s' % self.name)

	def serverterminal(self,inp): #used for server commands
		if inp:
			if inp == 'exit':
				self.exit()
			elif inp == 'clear':
				self.clear()
			elif inp == 'info':
				self.info(self)

	def exit(self): #kill all proceses for a tidy exit
		self.shouldExit = True

if __name__ == '__main__':
	CommonCode_Server.main(sys.argv[1:],TemplateServer)