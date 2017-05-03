import sys, socket, select, os, threading, getopt, random, sqlite3
from time import strftime, sleep
from datetime import datetime, timedelta

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
	serverport = 9099
	send_cache = 40960
	send_cache_enc = 40960
	RSA_bitlength = 2048
	shouldEncrypt = True
	shouldEncryptDownload = True
	scriptname = 'token'
	function = 'token_client'
	name = 'token'
	downloadAddrLoc = 'jedkos.com:9011&&protocols/token.py' 
	#form is ip:port&&location/on/filetransferserver/file.py
	tokenlength = 10

	def __init__(self, serve=serverport):
		CommonCode_Server.TemplateServer.__init__(self,serve)

	def init_spec(self):
		self.funcMap = {
			'create':self.createTokenCommand,
			'checkout':self.checkoutTokenCommand,
			'remove':self.removeTokenCommand
		}
		# insert application-specific initialization code here
		if not os.path.exists(__location__+'/resources/programparts/%s' % self.name): os.makedirs(__location__+'/resources/programparts/%s' % self.name)
		if not os.path.exists(__location__+'/resources/programparts/token/tokendatabase.sqlite3'):
			conn = sqlite3.connect(__location__+'/resources/programparts/token/tokendatabase.sqlite3')
			cur = conn.cursor()
			cur.execute('CREATE TABLE Tokens (token TEXT, server TEXT, creation INTEGER, expiration INTEGER, extra STRING)')
			conn.close()
		self.load_service_key()

	def serverterminal(self,inp): #used for server commands
		if inp:
			if inp == 'exit':
				self.exit()
			elif inp == 'clear':
				self.clear()
			elif inp == 'info':
				self.info()

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

	def createAndInsertToken(self,server,duration):
		tokenstring = None
		try:
			conn = sqlite3.connect(__location__+'/resources/programparts/token/tokendatabase.sqlite3')
			cur = conn.cursor()

			chars = '1234567890!@#$%^&*ABCDEFGHIJKLMNOPQRSTUVWXYZ'
			exists = 'yes'
			while exists != None:
				tokenstring = ''
				for n in range(0,self.tokenlength):
					tokenstring += random.choice(chars)

				cur.execute('SELECT token from Tokens WHERE token=?',(tokenstring,))
				exists = cur.fetchone()

			#cur.execute('CREATE TABLE Tokens (token TEXT, server TEXT, creation INTEGER, expiration INTEGER, extra STRING)')

			creationDate = datetime.utcnow()
			creation = creationDate.strftime("%Y%m%d%H%M%S")
			expirationDate = creationDate+timedelta(hours=23,minutes=59)
			expiration = expirationDate.strftime("%Y%m%d%H%M%S")

			extra = ''
			cur.execute('INSERT INTO Tokens (token, server, creation, expiration, extra) VALUES (?,?,?,?,?)', (tokenstring,server,creation,expiration,extra))
			conn.commit()
		except Exception,e:
			print str(e)
			tokenstring = None

		return tokenstring

	def checkIfValidToken(self,requested_token,service_name):
		valid = False
		try:
			conn = sqlite3.connect(__location__+'/resources/programparts/token/tokendatabase.sqlite3')
			cur = conn.cursor()
			cur.execute('SELECT expiration from Tokens WHERE token=? and server=?',(requested_token,service_name))
			expiration = cur.fetchone()

			if expiration == None:
				print 'could not find token!'
				return False
			expiration = expiration[0]

			print expiration
			nowtime = int(datetime.utcnow().strftime("%Y%m%d%H%M%S"))
			print nowtime
			if expiration > nowtime:
				print 'valid!'
				self.removeToken(requested_token,service_name)
				return True

		except Exception,e:
			print str(e)
		print 'is: %s' % valid
		return valid

	def removeToken(self,requested_token,service_name):
		try:
			conn = sqlite3.connect(__location__+'/resources/programparts/token/tokendatabase.sqlite3')
			cur = conn.cursor()
			cur.execute('DELETE FROM Tokens WHERE token=? and server=?',(requested_token,service_name))
			conn.commit()

		except Exception,e:
			print str(e)

	def checkoutTokenCommand(self,s):
		requested_token,service_name = s.recv(128).split('|')
		valid = self.checkIfValidToken(requested_token,service_name)
		if valid:
			s.send('y')
		else:
			s.send('n')
			s.recv(2)
			s.sendall('invalid')

	def createTokenCommand(self,s):
		s.recv(2)
		susername,spassword = self.load_service_key()
		if susername == None:
			s.sendall('n')
		else:
			s.sendall('y')
			username = s.recv(128)
			s.sendall('ok')
			password = s.recv(128)
			if susername == username and spassword == password:
				s.sendall('y')
			else:
				s.sendall('n')
				s.recv(2)
				s.sendall('invalid credentials')
				print 'invalid credentials'
				return
		data = s.recv(128)
		server,duration = data.split('|')
		token = self.createAndInsertToken(server,duration)
		if token != None:
			s.send('y')
			s.sendall(token)
			print 'token created and sent'
		else:
			s.send('n')
			print 'token NOT created and sent'

	def removeTokenCommand(self,s):
		requested_token,service_name = s.recv(128).split('|')
		if len(requested_token) > 0 and len(service_name) > 0:
			self.removeToken(requested_token,service_name)
		s.sendall('ok')

	def exit(self): #kill all proceses for a tidy exit
		self.shouldExit = True

if __name__ == '__main__':
	CommonCode_Server.main(sys.argv[1:],TemplateServer)
