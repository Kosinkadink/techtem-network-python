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

	scriptname = 'token'
	scriptfunction = 'token_client'
	version = '3.0.0'

	def __init__(self,location,startTerminal):
		global __location__
		__location__ = location
		CommonCode_Client.TemplateProt.__init__(self,location,startTerminal)

	def init_spec(self):
		self.funcMap = {
			'create':self.createTokenCommand,
			'checkout':self.checkoutTokenCommand,
			'remove':self.removeTokenCommand
		}
		#token files start
		if not os.path.exists(__location__+'/resources/programparts/token'): os.makedirs(__location__+'/resources/programparts/token')

		if not os.path.exists(__location__+'/resources/programparts/token/serverlist.txt'):
			with open(__location__+'/resources/programparts/token/serverlist.txt', "a") as seeds:
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
		if self.shouldEncrypt:
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
					elif inp.split()[0] == 'create':
						print self.connectNewToken(inp.split()[1],'1000')
					elif inp.split()[0] == 'checkout':
						print self.connectTokenValidity(inp.split()[1],inp.split()[2])
					elif inp.split()[0] == 'remove':
						print self.connectTokenRemove(inp.split()[1],inp.split()[2])
					
					else:
						print "Invalid command"
			except Exception,e:
				print str(e)

	def connectTokenValidity(self,requested_token,service_name):
		data = requested_token+'|'+service_name
		return self.connectToServer(data,'checkout')

	def connectTokenRemove(self,requested_token,service_name):
		data = requested_token+'|'+service_name
		return self.connectToServer(data,'remove')

	def connectNewToken(self,service_name,duration):
		data = service_name+'|'+duration
		return self.connectToServer(data,'create')


	def connectToServer(self,data,command):
		with open(__location__+'/resources/programparts/token/serverlist.txt', "r") as seeds:
			for line in seeds:
				if line.startswith('||'):
					#try: #connect to ip, save data, issue command
					return self.connectip(self,line.split("||")[1],data,command)
					#except Exception,e:
					print str(e) + "\n"
		print ''

	def load_service_key(self):
		susername = None
		spassword = None
		if not os.path.exists(__location__+'/resources/programparts/%s/service_key.txt' % self.name):
			with open(__location__+'/resources/programparts/%s/service_key.txt' % self.name, 'wb') as skey:
				skey.write("#Username (choose one)\n")
				skey.write("#Password (choose one)\n")
		else:
			with open(__location__+'/resources/programparts/%s/service_key.txt' % self.name, 'r') as skey:
				for line in skey:
					try:
						if line.startswith('Username'):
							susername = line.strip().split()[1]
						elif line.startswith('Password'):
							spassword = line.strip().split()[1]
					except Exception,e:
						print str(e)
		return (susername,spassword)

	def checkoutTokenCommand(self,s,data):
		s.sendall(data)
		valid = s.recv(1)
		if valid == 'y':
			return True
		else:
			s.sendall('ok')
			error = s.recv(128)
			print error
			return False

	def createTokenCommand(self,s,data):
		s.send('ok')
		has_skey = s.recv(1)
		if has_skey == 'y':
			susername,spassword = self.load_service_key()
			s.sendall(susername)
			s.recv(2)
			s.sendall(spassword)
			valid = s.recv(1)
			if valid != 'y':
				s.sendall('ok')
				error = s.recv(128)
				print error
				return error
		s.sendall(data)
		created = s.recv(1)
		if created == 'y':
			token = s.recv(128)
			return token
		else:
			print 'did not successfully create token on server'
			return None

	def removeTokenCommand(self,s,data):
		s.sendall(data)
		s.recv(2)		
			
	def exit(self):
		quit()

def standalone_function(data,location,startTerminal):
	TemplateProt(location,startTerminal)
	return "Left token client, back in main client"

def server_function(location):
	return TemplateProt(location,False)

if __name__ == "__main__":
	location = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__))) #directory from which this script is ran
	if os.name == 'nt':
		location = location.replace('\\','/')
	TemplateProt(location,True)
