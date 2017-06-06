#!/usr/bin/python2
import sys, socket, select, os, threading, urllib2, urllib, getopt, copy
from time import strftime, sleep
try:
	from Crypto.Cipher import AES
	from Crypto import Random
	from Crypto.PublicKey import RSA
	from Crypto.Cipher import PKCS1_OAEP
except ImportError:
	print "NOTICE: PyCrypto not found on Python 2.7; try the command 'pip install pycrypto' or find the package online"
	print "Connections will NOT be encrypted"

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
	serverport = 9012
	send_cache = 40960
	send_cache_enc = 40960
	RSA_bitlength = 2048
	shouldEncrypt = True
	shouldEncryptDownload = True
	scriptname = 'wwwrequest'
	function = 'wwwrequest_client'
	name = 'wwwrequest'
	downloadAddrLoc = 'jedkos.com:9011&&protocols/wwwrequest.py'
	#form is ip:port&&location/on/filetransferserver/file.py

	def __init__(self, serve=serverport):
		CommonCode_Server.TemplateServer.__init__(self,serve)

	def init_spec(self):
		self.funcMap = {'request':self.wwwrequest_server}
		### server specific files start ###
		if not os.path.exists(__location__+'/resources/programparts/wwwrequest'): os.makedirs(__location__+'/resources/programparts/wwwrequest')
		if not os.path.exists(__location__+'/resources/programparts/wwwrequest/approvedfiles.txt'):
			with open(__location__+'/resources/programparts/wwwrequest/approvedfiles.txt', "a") as makeprot:
				makeprot.write("")
		### server specific files end ###

	def serverterminal(self,inp): #used for server commands
		if inp:
			if inp == 'exit':
				self.exit()
			elif inp == 'clear':
				self.clear()
			elif inp == 'info':
				self.info()

	def sendWebsite(self,s,website): #send file to seed

		if s.getKey() == None:
			use_cache = self.send_cache
		else:
			use_cache = self.send_cache_enc

		s.recv(2)
		s.sendall('%16d' % use_cache)
		s.recv(2)

		filelength = len(website)
		s.sendall('%16d' % filelength)

		print " sending..."
		sent = 0
		while True:
			try:
				sys.stdout.write(str((float(sent)/filelength)*100)[:4]+ '%   ' + str(sent) + '/' + str(filelength) + ' B\r')
				sys.stdout.flush()
			except:
				pass
			data = website[sent:sent+use_cache]
			if data == '':
				break
			sent += len(data)
			s.sendall(data)

		s.recv(2)
		sys.stdout.write('100.0%   ' + str(sent) + '/' + str(filelength) + ' B\n')
		print "sending successful"
			

	def wwwrequest_server(self,s):

		clientsocket = s									   

		file_name = s.recv(1024)

		try:
			website = urllib2.urlopen(file_name) #look up website
			print 'success'

		except Exception,e:
			print str(e)
			s.sendall('no')
		else:
			print "website found"
			s.sendall('ok')
			website = website.read()
			self.sendWebsite(s,website)

	def exit(self): #kill all proceses for a tidy exit
		self.shouldExit = True

if __name__ == '__main__':
	CommonCode_Server.main(sys.argv[1:],TemplateServer)