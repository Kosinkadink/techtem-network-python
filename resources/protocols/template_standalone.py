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
	netPass = None
	password = None
	username = None
	send_cache = 40960
	send_cache_enc = 40960
	should_encrypt = False
	startTerminal = True
	scriptname = 'template'
	scriptfunction = 'template_client'
	version = '3.0.0'
	AES_keysize = 32 #16, 24, 32
	threads = []


	def __init__(self,location,startTerminal):
		global __location__
		__location__ = location
		CommonCode_Client.TemplateProt.__init__(self,location,startTerminal)

	def run_processes(self):
		if self.startTerminal:
			#now do server terminal
			self.serverterminal()

	def initialize(self):
		if not os.path.exists(__location__+'/resources'): os.makedirs(__location__+'/resources')
		if not os.path.exists(__location__+'/resources/protocols'): os.makedirs(__location__+'/resources/protocols') #for protocol scripts
		if not os.path.exists(__location__+'/resources/cache'): os.makedirs(__location__+'/resources/cache') #used to store info for protocols and client
		if not os.path.exists(__location__+'/resources/programparts'): os.makedirs(__location__+'/resources/programparts') #for storing protocol files
		if not os.path.exists(__location__+'/resources/uploads'): os.makedirs(__location__+'/resources/uploads') #used to store files for upload
		if not os.path.exists(__location__+'/resources/downloads'): os.makedirs(__location__+'/resources/downloads') #used to store downloaded files
		if not os.path.exists(__location__+'/resources/networkpass'): os.makedirs(__location__+'/resources/networkpass') #contains network passwords
		self.injectCommonCode()
		self.should_encrypt = self.checkIfCryptoExists()
		self.netPass = self.get_netPass(__location__)
		self.gen_protlist(__location__)
		self.init_spec()
		self.run_processes()

	def injectCommonCode(self):
		CommonCode_Client.__location__ = __location__
		self.clear = CommonCode.clear
		self.connectip = CommonCode_Client.connectip
		self.distinguishCommand = CommonCode_Client.distinguishCommand
		self.socketTem = CommonCode.socketTem
		self.checkIfCryptoExists = CommonCode.checkIfCryptoExists
		self.get_netPass = CommonCode.get_netPass
		self.gen_protlist = CommonCode.gen_protlist
		self.toggleEncrypt = CommonCode.toggleEncrypt
		self.netPass_check = CommonCode.netPass_check
		self.gen_AES_key = CommonCode.gen_AES_key
		self.createFileTransferProt = CommonCode.createFileTransferProt

	def init_spec(self):
		self.funcMap = {} #fill with string:functions pairs
		#token files start
		if not os.path.exists(__location__+'/resources/programparts/%s' % scriptname): os.makedirs(__location__+'/resources/programparts/%s' % scriptname)

		if not os.path.exists(__location__+'/resources/programparts/%s/serverlist.txt' % scriptname):
			with open(__location__+'/resources/programparts/%s/serverlist.txt' % scriptname, "a") as seeds:
				seeds.write("""####################################################
##The format is: ||ip:port||
##Files will be sent to and from these servers
##Only lines starting with || will be read
####################################################""")
		#token files end

	def boot(self):
		self.clear()
		print "TechTem Token Client started"
		print "Version " + self.version
		if self.should_encrypt:
			print "Encryption is ON"
		else:
			print "Encryption is OFF"
		print "Type help for command list\n"

	def help(self):
		print "\nclear: clears screen"
		print "exit: closes program"
		print "encrypt OR enc: toggle encryption status"
	
	def serverterminal(self):
		self.boot()
		while 1:
			inp = raw_input(">")
			try:
				if inp:
					if inp.split()[0] == 'quit' or inp.split()[0] == 'leave' or inp.split()[0] == 'exit':
						break
					elif inp.split()[0] == 'clear':
						self.boot()
					elif inp.split()[0] == 'netpass':
						self.get_netPass()
						print self.netPass
					elif inp.split()[0] in ['encrypt','enc']:
						self.shouldEncrypt = self.toggleEncrypt(self.shouldEncrypt)
					
					else:
						print "Invalid command"
			except Exception,e:
				print str(e)
			
	def exit(self):
		quit()

def standalone_function(data,location,startTerminal):
	TemplateProt(location,startTerminal)
	return "Left token client, back in main client"

def server_function(location):
	return TemplateProt(location,False)