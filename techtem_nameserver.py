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
	# change this to default values
	version = '3.0.0'
	serverport = 9010
	send_cache = 40960
	send_cache_enc = 40960
	RSA_bitlength = 2048
	shouldEncrypt = True
	shouldEncryptDownload = True
	scriptname = 'name'
	function = 'name_function'
	name = 'name'
	downloadAddrLoc = 'jedkos.com:9011&&protocols/name.py' 
	#form is ip:port&&location/on/filetransferserver/file.py

	def __init__(self, serve=serverport):
		CommonCode_Server.TemplateServer.__init__(self,serve)

	def init_spec(self):
		self.funcMap = {'name':self.name_server}
		# insert application-specific initialization code here
		if not os.path.exists(__location__+'/resources/programparts/%s/' % self.name): os.makedirs(__location__+'/resources/programparts/%s/' % self.name)
		if not os.path.exists(__location__+'/resources/programparts/%s/techtemurls.txt' % self.name):
			with open(__location__+'/resources/programparts/%s/techtemurls.txt' % self.name, 'wb') as urls:
				urls.write('## list name to ip in this format: ||name||ip:port||')

	def serverterminal(self,inp): #used for server commands
		if inp:
			if inp == 'exit':
				self.exit()
			elif inp == 'clear':
				self.clear()
			elif inp == 'info':
				self.info()

	def searchurls(self,rqst):
		exists = False
		with open(__location__+'/resources/programparts/name/techtemurls.txt') as file:
			for line in file:
				if line.startswith('||'):
					url = line.split("||")
					if url[1] == rqst:
						ip = url[2]
						exists = True
						break
		if exists:
			return (True,ip)
		else:
			return (False,'name does not exist')

	def name_server(self,s):
		rqst = s.recv(1024)
		print "Requested name: " + rqst
		success,message = self.searchurls(rqst.lower())
		if success:
			s.sendall('y')
			s.recv(2)
			print "Corresponding IP: " + message
			s.sendall(message)
		if not success:
			s.sendall('n')
			s.recv(2)
			s.sendall(message)

	def exit(self): #kill all proceses for a tidy exit
		self.shouldExit = True

if __name__ == '__main__':
	CommonCode_Server.main(sys.argv[1:],TemplateServer)