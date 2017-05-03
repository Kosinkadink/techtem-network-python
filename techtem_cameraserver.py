import sys, socket, select, os, threading, getopt, pickle, numpy
from time import strftime, sleep
try:
	import cv2
except ImportError:
	print "ERROR: OpenCV 3.0.0 or above not found, please install and try again."
	quit()

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

class VideoStream(threading.Thread):

	def __init__(self,buffer,s):
		threading.Thread.__init__(self)
		self.buffer = buffer
		self.s = s
		self.frameLock = threading.Lock()
		self.readNewFrame = threading.Event()
		self.event = threading.Event()
		self.shouldDelete = False
		#print "buffer: %s " % str(self.buffer)

	def run(self):
		self.sendFramesLoop()

	def sendFramesLoop(self):
		while not self.event.is_set():
			sleep(0.05)
			if self.readNewFrame.is_set():
				#send the frame
				try:
					frameEnc = self.buffer[0]
					size = '%16d' % len(frameEnc)
					self.s.sendall(size)
					self.s.sendall(frameEnc)
				except Exception,e:
					print 'ERROR in stream: %s' % str(e)
					self.event.set()
				else:
					self.readNewFrame.clear()
		self.s.close()
		self.shouldDelete = True


class CameraObject(threading.Thread):
	#VideoStreams that wish to get in on the action
	streams = []
	#functions_to_perform = [(cv2.resize,'k',{'dsize':(0,0), 'fx':0.5, 'fy':0.5}),
	#						(cv2.cvtColor,'a',(cv2.COLOR_BGR2GRAY,))]
	functions_to_perform = [(cv2.resize,'k',{'dsize':(0,0), 'fx':0.5, 'fy':0.5}),
							(cv2.cvtColor,'a',(cv2.COLOR_BGR2RGB,))]

	def __init__(self, cap, name='CameraStream', bufferSize=20, show=False):
		threading.Thread.__init__(self)
		self.event = threading.Event()
		self.name = name
		self.cap = cap
		self.bufferSize = bufferSize
		self.buffer = [""]*self.bufferSize
		self.currIndex = 0
		self.keepRunning = True
		self.show = show
		self.streamLock = threading.Lock()
		self.width = None
		self.height = None

	def run(self):
		self.cameraLoop()

	def cameraLoop(self):
		while self.keepRunning and not self.event.is_set():
			#print 'getting frame...'
			ret,frame = self.cap.read()
			#print 'done getting frame!'
			if ret:
				for funcTuple in self.functions_to_perform:
					if funcTuple[1] == 'a':
						frame = funcTuple[0](frame,*funcTuple[2])
					elif funcTuple[1] == 'k':
						frame = funcTuple[0](frame,**funcTuple[2])
				#frame = cv2.resize(frame, (0,0), fx = 0.4, fy = 0.4)
				h,w = frame.shape[:2]
				if self.width != w:
					self.width = w
				if self.height != h:
					self.height = h
				#insert in front, remove extra end
				#encode image
				frameEnc = cv2.imencode('.jpg',frame)[1]
				#frameEnc = frame
				
				#print type(frameEnc)
				#imgJPG = StringIO.StringIO()
				#cv2.imwrite(imgJPG,frameEnc,)
				frameEnc = pickle.dumps(frameEnc)
				#print type(frameEnc)
				#print len(frameEnc)
				#self.buffer.insert(0,zlib.compress(frameEnc.tobytes()))
				self.buffer.insert(0,frameEnc)
				self.buffer.pop()
				#self.currIndex = (self.currIndex+1)%self.bufferSize
				if self.show:
					#print 'going to show image... %s' % self.name
					frameDec = cv2.imdecode(frameEnc,1)
					#frameDec = frameEnc
					cv2.imshow(self.name, frameDec)
					#print 'going to start windows thread...'
					cv2.startWindowThread()
				self.updateStreams()

			#count += 1
			#count = count%capObj.frame_num
			if not ret:
				#print 'could not get frame, waiting...'
				pass
			#print 'waiting for key...'
			key = cv2.waitKey(50) & 0xFF
			if self.show:
				if key == ord('q'):
					self.stopCamera()
		#stop all streams
		self.stopAllStreams()
		#release cam capture
		self.cap.release()
		if self.show:
			cv2.destroyWindow(self.name)
		del self.buffer

	def add_mod_func(self):
		pass

	def remove_mod_func_index(self,index):
		pass

	def add_request_stream(self,s):
		sizeString = str(self.width) + ',' + str(self.height)
		print sizeString
		s.sendall(sizeString)
		s.recv(2)
		newStream = VideoStream(self.buffer,s)
		newStream.daemon = True
		newStream.start()
		self.streamLock.acquire()
		self.streams.append(newStream)
		self.streamLock.release()

	def updateStreams(self):
		to_be_deleted = []
		for stream in self.streams:
			if stream.shouldDelete:
				to_be_deleted.append(stream)
			else:
				stream.readNewFrame.set()
		for stream in to_be_deleted:
			self.streamLock.acquire()
			self.streams.remove(stream)
			self.streamLock.release()
			print 'broken stream removed successfully'

	def stopAllStreams(self):
		for stream in self.streams:
			stream.event.set()

	def stopCamera(self):
		self.event.set()


class TemplateServer(CommonCode_Server.TemplateServer):

	# don't change this
	netPass = None
	key = None
	pubkey = None
	threads = []
	startTime = None
	# change this to default values
	version = '3.0.0'
	serverport = 9040
	send_cache = 40960
	send_cache_enc = 40960
	RSA_bitlength = 2048
	shouldEncrypt = True
	shouldEncryptDownload = True
	scriptname = 'camera'
	function = 'camera_function'
	name = 'camera'
	downloadAddrLoc = 'jedkos.com:9011&&protocols/camera.py' 
	#form is ip:port&&location/on/filetransferserver/file.py

	def __init__(self, serve=serverport):
		CommonCode_Server.TemplateServer.__init__(self,serve)
		#camera specific
		self.caps_keep_on = True
		self.cap_count = 0
		self.caps_names = []
		self.capDict = {}
		self.caps = []
		self.frame_num = 60
		self.show = True
		self.capLock = threading.Lock()
		self.nameLock = threading.Lock()
		self.nameCount = 0

	def init_spec(self):
		self.funcMap = {'start':self.startCommand,
					'stop':self.stopCommand,
					'avail':self.availCommand,
					'watch':self.watchCommand}
		# insert application-specific initialization code here
		if not os.path.exists(__location__+'/resources/programparts/%s' % self.name): os.makedirs(__location__+'/resources/programparts/%s' % self.name)

	def serverterminal(self,inp): #used for server commands
		try:
			if inp:
				if inp == 'exit':
					self.exit()
				elif inp == 'clear':
					self.clear()
				elif inp == 'info':
					self.info()
				elif inp.split()[0] == 'startcam':
					try:
						if inp.split()[1].strip() == "":
							print "ERROR: must be a number"
							return
						camNum = int(inp.split()[1])
					except ValueError:
						print "ERROR: must be a number"
						return
					success,msg = self.startCameraThread(camNum)
					if not success:
						print 'ERROR: %s' % msg
					else:
						print 'successfully started camera index %s' % msg

				elif inp.split()[0] == 'stopcam':
					try:
						camNum = int(inp.split()[1])
					except ValueError:
						print "ERROR: must be a number"
					else:
						print 'attempting to stop camera...'
						success,msg = self.stopCameraThread(camNum)
						if not success:
							print 'ERROR stopping cam thread %s: %s' % (camNum,msg)
						else:
							print 'successfully stopped camera index %s' % camNum 
		except Exception,e:
			print str(e)	

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

	def startCameraThread(self,camIndex):
		if str(camIndex) in self.capDict:
			return (False,'cap with index %s is already open' % camIndex)
		#start up a camera thread, add it to the dictionary
		try:
			#see if cap can be opened
			print 'trying to open video capture'
			temp_cap = cv2.VideoCapture(int(camIndex))
			print 'video capture open'
		except Exception,e:
			return (False,'exception when attempting to start index %s: %s' % (camIndex,str(e)))
		if not temp_cap.isOpened():
			return (False,'could not open desired cam index %s - not plugged in?' % camIndex)
		self.nameLock.acquire()
		camObj = CameraObject(temp_cap,name=str(self.nameCount),show=False)
		self.nameCount += 1
		self.nameLock.release()
		print 'camobj created'
		camObj.daemon = True
		camObj.start()
		print 'camobj started'
		self.capLock.acquire()
		self.capDict.setdefault(str(camIndex),camObj)
		self.capLock.release()
		print 'camobj added to dict'
		return (True,camIndex)

	def stopCameraThread(self,camIndex):
		exists = False
		self.capLock.acquire()
		camObj = self.capDict.pop(str(camIndex),None)
		if camObj != None:
			exists = True
			camObj.stopCamera()
		self.capLock.release()
		if exists != True:
			return (False,'cap with index %s does not exist' % camIndex)
		else:
			return (True,camIndex)

	def startCommand(self,s):
		## Check credentials, perform command if appropriate
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
		cameraReq = s.recv(128)
		success,msg = self.startCameraThread(cameraReq)
		if not success:
			s.sendall('n')
			s.recv(2)
			s.sendall(msg)
		else:
			s.sendall('y')

	def stopCommand(self,s):
		## Check credentials, perform command if appropriate
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
		cameraReq = s.recv(128)
		success,msg = self.stopCameraThread(cameraReq)
		if not success:
			s.sendall('n')
			s.recv(2)
			s.sendall(msg)
		else:
			s.sendall('y')

	def availCommand(self,s):
		## Check credentials, perform command if appropriate
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
		s.recv(2)
		s.sendall(str(self.capDict.keys()))

	def watchCommand(self,s):
		## Check credentials, perform command if appropriate
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
		cameraReq = s.recv(128)
		if str(cameraReq) in self.capDict:
			#keep going
			print 'valid watch request'
			s.sendall('y')
			s.recv(2)
			print 'adding socket to camera request list'
			self.capDict[str(cameraReq)].add_request_stream(s)
		else:
			s.sendall('n')
			s.recv(2)
			s.sendall('camera index does not exist')
			print 'requested index %s does not exist' % cameraReq

	def stopAllCameras(self):
		for index in self.capDict.keys():
			self.stopCameraThread(index)

	def exit(self): #kill all proceses for a tidy exit
		print 'exiting now...'
		self.stopAllCameras()
		self.shouldExit = True

if __name__ == '__main__':
	CommonCode_Server.main(sys.argv[1:],TemplateServer)