#!/usr/bin/python2
import sys, socket, select, os, threading, sqlite3, pickle, numpy
from time import strftime, sleep, time
from hashlib import sha1, md5
from getpass import getpass
#pygame for video output
try:
	import pygame
except ImportError:
	print "Requires pygame to view video stream; try command 'pip install pygame' or find package online"
import cv2
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

	scriptname = 'camera'
	name = scriptname
	scriptfunction = 'camera_function'
	version = '3.0.0'

	def __init__(self,location,startTerminal):
		global __location__
		__location__ = location
		CommonCode_Client.TemplateProt.__init__(self,location,startTerminal)

	def run_processes(self):
		if self.startTerminal:
			self.serverterminal()

	def init_spec(self):
		self.funcMap = {
			'avail':self.availCommand,
			'start':self.startCommand,
			'stop':self.stopCommand,
			'watch':self.watchCommand
		}
		#spec files start
		if not os.path.exists(__location__+'/resources/programparts/%s' % self.scriptname): os.makedirs(__location__+'/resources/programparts/%s' % self.scriptname)
		#spec files end

	def boot(self):
		self.clear()
		print "TechTem Network Camera Manager started"
		print "Version " + self.version
		if self.shouldEncrypt:
			print "Encryption is ON"
		else:
			print "Encryption is OFF"
		print "Type help for command list\n"

	def help(self):
		print "encrypt OR enc: toggle encryption status"
		print "clear: clears screen"

	#function for client splash screen
	def serverterminal(self):
		self.boot()
		while 1:
			inp = raw_input(">")
			try:
				if inp:
					# TOGGLE ENCRYPTION
					if inp.split()[0] in ['encrypt','enc']:
						self.shouldEncrypt = self.toggleEncrypt(self.shouldEncrypt)
					# CHECK AVAILABLE CAMERAS
					elif inp.split()[0] in ['avail','available']:
						try:
							ip = inp.split()[1]
						except:
							print 'no ip provided'
						else:
							print self.connectip(self,ip,'','avail')
					# START A CAMERA
					elif inp.split()[0] in ['start']:
						try:
							ip = inp.split()[1]
							index = inp.split()[2]
						except:
							print 'no ip provided, or no index provided'
						else:
							print self.connectip(self,ip,index,'start')
					# STOP A CAMERA
					elif inp.split()[0] in ['stop']:
						try:
							ip = inp.split()[1]
							index = inp.split()[2]
						except:
							print 'no ip provided, or no index provided'
						else:
							print self.connectip(self,ip,index,'stop')
					# WATCH A CAMERA STREAM
					elif inp.split()[0] in ['watch']:
						try:
							ip = inp.split()[1]
							index = inp.split()[2]
						except:
							print 'no ip provided, or no index provided'
						else:
							print self.connectip(self,ip,index,'watch')
					# QUIT MASTER
					elif inp.split()[0] == 'quit' or inp.split()[0] == 'leave' or inp.split()[0] == 'exit':
						break
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

	def startCommand(self,s,data):
		s.sendall('ok')
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
		success = s.recv(1)
		if success == 'y':
			return 'successfully started camera index %s' % data
		else:
			s.sendall('ok')
			return s.recv(128)

	def stopCommand(self,s,data):
		s.sendall('ok')
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
		success = s.recv(1)
		if success == 'y':
			return 'successfully stopped camera index %s' % data
		else:
			s.sendall('ok')
			return s.recv(128)

	def availCommand(self,s,data):
		s.sendall('ok')
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
		s.sendall('ok')
		return s.recv(128)

	def viewRequestStream(self,s,data):
		pygame.init()
		clock = pygame.time.Clock()
		keepRunning = True
		streamName = "Stream from Camera %s" % data
		sizeString = s.recv(128)
		s.sendall('ok')
		width,height = sizeString.split(',')
		pic_size_buf = (int(height),int(width))
		pic_size = (int(width),int(height))
		screen = pygame.display.set_mode(pic_size)
		pygame.display.set_caption(streamName)
		while keepRunning:
			#sleep(0.05)
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					keepRunning = False
			
			ready_to_read,ready_to_write,in_error = CommonCode.selectTem([s],[],[],0)
			#display image when received
			for sock in ready_to_read:
				rawPicList = []
				size = s.recv(16)
				size = int(size.strip())
				#print size
				received = 0
				while keepRunning and received < size:
					rawPicPart = s.recv(1024000)
					if not rawPicPart:
						break
					else:
						rawPicList.append(rawPicPart)
						received += len(rawPicPart)
				rawPic = "".join(rawPicList)
				print len(rawPic)
				#rawPic = s.recv(1024000)
				#print len(rawPic)
				#print pic_size
				#print rawPic
				#rawPicArr = np.fromstring(rawPic)

				rawPickle = pickle.loads(rawPic)
				rawPicDec = cv2.imdecode(rawPickle,1)
				
				rawPicDec = numpy.rot90(rawPicDec)
				#print 'got a rawPic decoded'
				#cv2.imshow(streamName,rawPicDec)
				#rawPic = zlib.decompress(rawPic)
				#pic = pygame.image.fromstring(rawPic,pic_size,'RGB')
				#pic = pygame.Surface(pic_size_buf)
				#buf = pic.get_buffer()
				#buf.write(rawPicDec*1,0)
				#del buf

				pic = pygame.surfarray.make_surface(rawPicDec)
				
				screen.blit(pic,(0,0))
				pygame.display.flip()
			clock.tick(30)
		#except Exception,e:
			#	print 'ERROR in stream: %s' % str(e)
			#	keepRunning = False
		pygame.quit()

	def watchCommand(self,s,data):
		s.sendall('ok')
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
		success = s.recv(1)
		if success == 'y':
			#do stream stuff
			s.sendall('ok')
			print 'entering stream...'
			watch_thread = threading.Thread(target=self.viewRequestStream,args=(s,data))
			watch_thread.daemon = True
			watch_thread.start()
		else:
			s.sendall('ok')
			return s.recv(128)

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
