#!/usr/bin/python2
import sys, socket, select, os, threading, subprocess, getopt
from time import strftime, sleep, time
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

class TicTacToe2D(threading.Thread):

	def __init__(self,players,_id):
		threading.Thread.__init__(self)
		self.players = players
		self.event = threading.Event()
		self.isDone = False
		self._id = _id

	def run(self):
		self.checkIfClientsConnected()

	def markDone(self):
		self.isDone = True

	def checkIfClientsConnected(self):
		shouldStop = False
		for s in self.players:
			try:
				s.sendall('?')
				ready = s.recv(1)
			except Exception,e:
				print str(e)
				shouldStop = True
			if ready != 'y':
				shouldStop = True
		if shouldStop:
			for s in self.players:
				try:
					s.sendall('DSCNCT||a player has left')
				except Exception,e:
					print str(e)
			self.markDone()
		else:
			reason = self.playGame()
			for s in self.players:
				try:
					s.sendall('DSCNCT||%s' % reason)
				except Exception,e:
					print str(e)
			self.markDone()

	def playGame(self):
		prop = ['0','1','2','3','4','5','6','7','8']
		mark = ['X','O']
		b = [' ']*9
		turn = 0

		newboard,win,winner = self.gameboard2d(b)

		print 'two users in a match'
		for sock in socklist:
			try:
				sock.sendall('b||' + newboard)
				sock.recv(5)
			except:
				print 'a player has left'
				return 'a player has left'

		while not self.event.is_set():
			sleep(.1)
			
			ready_to_read,ready_to_write,in_error = CommonCode.selectTem(self.players,[],[],0)
			for sock in ready_to_read:
				playerReq = socklist.index(sock)
				try:
					data = sock.recv(1024)
				except Exception,e:
					print str(e)
					print 'a bad playa disconnected, game disbanded $%$%$'
					return 'a player has left'
				#if received data, continue processing
				if data:
					if data == 'EXIT':
						print 'player %s has left' % mark[playerReq]
						return 'player %s has left' % mark[playerReq]
					#check if it is player's turn
					if playerReq == turn % 2:
						#check if message was a valid position
						if data in prop:
							if b[int(data)] == ' ':
								b[int(data)] = mark[turn % 2]
							else:
								sock.sendall('e||Position already full. Choose a different position.')
								continue
						else:
							sock.sendall('e||Not a valid position')
							continue
						
						newboard,win,winner = self.gameboard2d(b)
						for sock2 in socklist:
							try:
								sock2.sendall('b||' + newboard)
								sock2.recv(5)
							except:
								print 'a poor player has left, game disbanded'
								return
						if win:
							for sock2 in socklist:
								try:
									sock2.sendall('w||%s has won!' % winner)
									sock.recv(5)
								except:
									print 'a sour loser has left, still counts ;)'
									return
							print "game is over!"
							return
						turn += 1
						if turn >= 9:
							for sock2 in socklist:
								try:
									sock2.sendall('w||Tie!')
									sock2.recv(5)
								except:
									print 'a player has left, still a tie though'
									return
							print "game is over!"
							return
					else:
						sock.sendall('e||It is not your turn')
						continue
				else:
					print 'a player has left'
					for sock2 in socklist:
						try:
							sock2.sendall('x||')
							sock2.recv(5)
						except:
							pass
					return

	def gameboard2d(self,b):
		board = ''
		lines = []
		lines += ["  - - - - - -"]
		lines += [" | %s | %s | %s |" % (0,1,2)]
		lines += ["  - - - - - -"]
		lines += [" | %s | %s | %s |" % (3,4,5)]
		lines += ["  - - - - - -"]
		lines += [" | %s | %s | %s |" % (6,7,8)]
		lines += ["  - - - - - -"] 
		lines += ['']
		lines += ["  - - - - - -"]
		lines += [" | %s | %s | %s |" % (b[0],b[1],b[2])]
		lines += ["  - - - - - -"]
		lines += [" | %s | %s | %s |" % (b[3],b[4],b[5])]
		lines += ["  - - - - - -"]
		lines += [" | %s | %s | %s |" % (b[6],b[7],b[8])]
		lines += ["  - - - - - -"] 
		for line in lines:
			board += line + '\n'
			win,winner = self.check_win(b)
		return (board,win,winner)

	def check_win(self,b):
		if b[0] != ' ':
			if b[0] == b[1] and b[0] == b[2]:
				return (True,b[0])
			if b[0] == b[3] and b[0] == b[6]:
				return (True,b[0])
		if b[4] != ' ':
			if b[0] == b[4] and b[0] == b[8]:
				return (True,b[4])
			if b[2] == b[4] and b[2] == b[6]:
				return (True,b[4])
			if b[1] == b[4] and b[1] == b[7]:
				return (True,b[4])
			if b[3] == b[4] and b[3] == b[5]:
				return (True,b[4])
		if b[8] != ' ':
			if b[2] == b[8] and b[2] == b[5]:
				return (True,b[8])
			if b[6] == b[8] and b[6] == b[7]:
				return (True,b[8])
		return (False,None)

class GameTicTacToe(object):

	def __init__(self,maxPlayers,boardSize):
		self.marks = []
		self.b = [' ']*boardSize
		self.prop = range(0,boardSize)
		self.prop[:] = [str(num) for num in self.prop]
		self.turn = 0
		self.maxPlayers = maxPlayers

	def check_win2D(self,b):
		if b[0] != ' ':
			if b[0] == b[1] and b[0] == b[2]:
				return (True,b[0])
			if b[0] == b[3] and b[0] == b[6]:
				return (True,b[0])
		if b[4] != ' ':
			if b[0] == b[4] and b[0] == b[8]:
				return (True,b[4])
			if b[2] == b[4] and b[2] == b[6]:
				return (True,b[4])
			if b[1] == b[4] and b[1] == b[7]:
				return (True,b[4])
			if b[3] == b[4] and b[3] == b[5]:
				return (True,b[4])
		if b[8] != ' ':
			if b[2] == b[8] and b[2] == b[5]:
				return (True,b[8])
			if b[6] == b[8] and b[6] == b[7]:
				return (True,b[8])
		return (False,None)

	def make_move(self,index):
		if str(index) not in self.prop:
			return False
		if self.b[int(index)] != ' ':
			return False
		else:
			self.b[int(index)] = marks[self.turn%self.maxPlayers]
			self.turn += 1
			return True

	def check_win(self):
		#placeholder function
		return (False,None)


class GameTicTacToe2D(GameTicTacToe):

	def __init__(self):
		GameTicTacToe.__init__(self,2,9)
		self.marks = ['X','O']

	#return (ifWon, whoWon)
	def check_win(self):
		return self.check_win2D(self.b)

class GameTicTacToe3D(GameTicTacToe):

	def __init__(self):
		GameTicTacToe.__init__(self,3,27)
		self.marks = ['X','O','F']

	def check_win(self):
		win,winner = self.check_win2D(self.b[0:9])
		if win:
			return (win,winner)
		win,winner = self.check_win2D(self.b[9:18])
		if win:
			return (win,winner)
		win,winner = self.check_win2D(self.b[18:])
		if win:
			return (win,winner)
		win,winner = self.check_win2D([self.b[0],self.b[1],self.b[2],self.b[9],self.b[10],self.b[11],self.b[18],self.b[19],self.b[20]])
		if win:
			return (win,winner)
		win,winner = self.check_win2D([self.b[0+3],self.b[1+3],self.b[2+3],self.b[9+3],self.b[10+3],self.b[11+3],self.b[18+3],self.b[19+3],self.b[20+3]])
		if win:
			return (win,winner)
		win,winner = self.check_win2D([self.b[0+6],self.b[1+6],self.b[2+6],self.b[9+6],self.b[10+6],self.b[11+6],self.b[18+6],self.b[19+6],self.b[20+6]])
		if win:
			return (win,winner)
		win,winner = self.check_win2D([self.b[0],self.b[3],self.b[6],self.b[9],self.b[12],self.b[15],self.b[18],self.b[21],self.b[24]])
		if win:
			return (win,winner)
		win,winner = self.check_win2D([self.b[0+1],self.b[3+1],self.b[6+1],self.b[9+1],self.b[12+1],self.b[15+1],self.b[18+1],self.b[21+1],self.b[24+1]])
		if win:
			return (win,winner)
		win,winner = self.check_win2D([self.b[0+2],self.b[3+2],self.b[6+2],self.b[9+2],self.b[12+2],self.b[15+2],self.b[18+2],self.b[21+2],self.b[24+2]])
		if win:
			return (win,winner)
		if self.b[13] != ' ':
			if self.b[0] == self.b[13] and self.b[0] == self.b[26]:
				return (True,self.b[13])
			if self.b[2] == self.b[13] and self.b[2] == self.b[24]:
				return (True,self.b[13])
			if self.b[6] == self.b[13] and self.b[6] == self.b[20]:
				return (True,self.b[13])
			if self.b[8] == self.b[13] and self.b[8] == self.b[18]:
				return (True,self.b[13])
		return (False,None)



class TicTacToe3D(threading.Thread):

	def __init__(self,players,_id):
		threading.Thread.__init__(self)
		self.players = players
		self.event = threading.Event()
		self.isDone = False
		self._id = _id


class MatchMaker(threading.Thread):

	def __init__(self,reqParticipants,classToUse):
		threading.Thread.__init__(self)
		self.reqParts = reqParticipants
		self.classToUse = classToUse
		self.matchDict = {}
		self.partQueue = []
		self.queueLock = threading.Lock()
		self.matchLock = threading.Lock()
		self.event = threading.Event()
		self.currID = 0

	def run(self):
		self.manageMatches()

	def addParticipant(self,s):
		self.queueLock.acquire()
		self.partQueue.append(s)
		self.queueLock.release()

	def close(self):
		self.event.set()

	def manageMatches(self):
		while not self.event.is_set()
			sleep(0.5)
			while len(partQueue) >= reqParticipants:
				#start a game that will take care of the rest of stuff
				self.createMatch()
			self.removeDoneMatches()

	def createMatch(self):
		self.queueLock.acquire()
		#add required num to game, remove them from queue
		newMatch = self.classToUse(self.partQueue[0:reqParticipants],str(currID))
		newMatch.daemon = True
		newMatch.start()
		self.matchDict.setdefault(str(currID),newMatch)
		del self.partQueue[0:reqParticipants]
		self.currID += 1
		self.queueLock.release()

	def removeDoneMatches(self):
		keys_to_remove = []
		for _id,match in self.matchDict.iteritems():
			if match.isDone:
				keys_to_remove.append(_id)
		for key in keys_to_remove:
			self.matchLock.acquire()
			self.matchLock.pop(key)
			self.matchLock.release()
				


class TicTacServer(CommonCode_Server.TemplateServer):


	# change this to default values
	version = '3.0.0'
	serverport = 9020
	send_cache = 40960
	send_cache_enc = 40960
	RSA_bitlength = 2048
	shouldEncrypt = True
	shouldEncryptDownload = True
	scriptname = 'tiactac'
	function = 'tictac_client'
	name = 'tictac'
	downloadAddrLoc = 'jedkos.com:9011&&protocols/tictac.py'
	#form is ip:port&&location/on/filetransferserver/file.py
	socketlist2d = []
	socketlist3d = []
	addrlist2d = []
	addrlist3d = []

	def __init__(self, serve=serverport):
		CommonCode_Server.TemplateServer.__init__(self,serve)

	def run(self):
		self.initialize()

	def run_processes(self):
		serverprocess = threading.Thread(target=self.servergen)
		self.threads.append(serverprocess)
		serverprocess.daemon = True
		serverprocess.start() #starts server process in another thread

		tictac2dprocess = threading.Thread(target=self.tictac2dthread)
		self.threads.append(tictac2dprocess)
		tictac2dprocess.daemon = True
		tictac2dprocess.start() #starts tictac2d thread

		tictac3dprocess = threading.Thread(target=self.tictac3dthread)
		self.threads.append(tictac3dprocess)
		tictac3dprocess.daemon = True
		tictac3dprocess.start() #starts tictac3d thread

		self.serverterminal() #starts command input

	def init_spec(self):
		self.funcMap = {'2d':self.playerqueue2d,
						'3d':self.playerqueue3d}
		### server specific files start ###
		### server specific files end ###
		self.gen_RSA_key()

	def serverterminal(self,inp): #used for server commands
		if inp:
			if inp == 'exit':
				self.exit()
			elif inp == 'clear':
				self.clear()
			elif inp == 'info':
				self.info()

	def tictac2d(self,socklist,addrlist):
		prop = ['0','1','2','3','4','5','6','7','8']
		mark = ['X','O']
		b = [' ']*9
		turn = 0

		newboard,win,winner = self.gameboard2d(b)

		print 'two users in a match'
		for sock in socklist:
			try:
				sock.sendall('b||' + newboard)
				sock.recv(5)
			except:
				print 'a player has left'
				return

		while 1:
			sleep(.1)
			
			ready_to_read,ready_to_write,in_error = select.select(socklist,[],[],0)
			for sock in ready_to_read:
				addr = addrlist[socklist.index(sock)]
				playerReq = socklist.index(sock)

				try:
					data = sock.recv(1024)
				except:
					print 'a bad playa disconnected, game disbanded $%$%$'
					return
				if data:
					if playerReq == turn % 2:
						if data.startswith('/exit'):
							for sock2 in socklist:
								if sock != sock2:
									try:
										sock2.sendall('player %s has left the match, game disbanded' % mark[playerReq])
										return
									except:
										print 'both players have left, game disbanded'
										return
						else:
							if data in prop:
								if b[int(data)] == ' ':
									b[int(data)] = mark[turn % 2]
								else:
									sock.sendall('e||Position already full. Choose a different position.')
									continue
							else:
								sock.sendall('e||Not a valid position')
								continue
						#sock.sendall('message received')
						newboard,win,winner = self.gameboard2d(b)
						for sock2 in socklist:
							try:
								sock2.sendall('b||' + newboard)
								sock2.recv(5)
							except:
								print 'a poor player has left, game disbanded'
								return
						if win:
							for sock2 in socklist:
								try:
									sock2.sendall('w||%s has won!' % winner)
									sock.recv(5)
								except:
									print 'a sour loser has left, still counts ;)'
									return
							print "game is over!"
							return
						turn += 1
						if turn >= 9:
							for sock2 in socklist:
								try:
									sock2.sendall('w||Tie!')
									sock2.recv(5)
								except:
									print 'a player has left, still a tie though'
									return
							print "game is over!"
							return
					else:
						sock.sendall('e||It is not your turn')
						continue
				else:
					print 'a player has left'
					for sock2 in socklist:
						try:
							sock2.sendall('x||')
							sock2.recv(5)
						except:
							pass
					return




	def gameboard2d(self,b):
		board = ''
		lines = []
		lines += ["  - - - - - -"]
		lines += [" | %s | %s | %s |" % (0,1,2)]
		lines += ["  - - - - - -"]
		lines += [" | %s | %s | %s |" % (3,4,5)]
		lines += ["  - - - - - -"]
		lines += [" | %s | %s | %s |" % (6,7,8)]
		lines += ["  - - - - - -"] 
		lines += ['']
		lines += ["  - - - - - -"]
		lines += [" | %s | %s | %s |" % (b[0],b[1],b[2])]
		lines += ["  - - - - - -"]
		lines += [" | %s | %s | %s |" % (b[3],b[4],b[5])]
		lines += ["  - - - - - -"]
		lines += [" | %s | %s | %s |" % (b[6],b[7],b[8])]
		lines += ["  - - - - - -"] 
		for line in lines:
			board += line + '\n'
			win,winner = self.check_win(b)
		return (board,win,winner)

	def check_win(self,b):
		if b[0] != ' ':
			if b[0] == b[1] and b[0] == b[2]:
				return (True,b[0])
			if b[0] == b[3] and b[0] == b[6]:
				return (True,b[0])
		if b[4] != ' ':
			if b[0] == b[4] and b[0] == b[8]:
				return (True,b[4])
			if b[2] == b[4] and b[2] == b[6]:
				return (True,b[4])
			if b[1] == b[4] and b[1] == b[7]:
				return (True,b[4])
			if b[3] == b[4] and b[3] == b[5]:
				return (True,b[4])
		if b[8] != ' ':
			if b[2] == b[8] and b[2] == b[5]:
				return (True,b[8])
			if b[6] == b[8] and b[6] == b[7]:
				return (True,b[8])
		return (False,None)


	def tictac3d(self,socklist,addrlist):
		print 'three users in a match'
		for sock in socklist:
			try:
				sock.sendall('match can begin')
			except:
				print 'a player has left'
				return
		#while 1 and not self.event.is_set():
		while 1:
			sleep(.1)
			
			ready_to_read,ready_to_write,in_error = select.select(socklist,[],[],0)
			for sock in ready_to_read:
				addr = addrlist[socklist.index(sock)]

				try:
					data = sock.recv(1024)
				except:
					print 'a bad playa disconnected, game disbanded $%$%$'
					return
				if data:
					sock.sendall('message received')
					for sock2 in socklist:
						if sock != sock2:
							try:
								sock2.sendall(data)
							except:
								'a poor player has left, game disbanded'
								return

	def tictac2dthread(self):
		while 1:
			sleep(0.1)
			while len(self.socketlist2d) >= 2:
				playersReady = 0
				for sock in self.socketlist2d[0:2]:
					sock.sendall('ready?')
					try:
						response = sock.recv(16)
					except:
						print 'A player has disconnected from the 2d queue'
					if response:
						playersReady += 1
					else:
						if sock in self.socketlist2d:
							self.addrlist2d.remove(self.addrlist2d[self.socketlist2d.index(sock)])
							self.socketlist2d.remove(sock)
							print 'A player has disconnected from the 2d queue (2nd option)'
				if playersReady == 2:
					print 'a game can begin'

					tictac2dgame = threading.Thread(target=self.tictac2d,args=(self.socketlist2d[0:2],self.addrlist2d[0:2]))
					tictac2dgame.daemon = True
					tictac2dgame.start() #starts tictac2d thread

					del self.socketlist2d[0:2]
					del self.addrlist2d[0:2]
				else:
					print 'a game can not begin; player count is only %s' % str(playersReady)
					for sock in self.socketlist2d:
						sock.sendall('waiting for additional players')

	def tictac3dthread(self):
		while 1:
			sleep(0.1)
			while len(self.socketlist3d) >= 3:
				playersReady = 0
				for sock in self.socketlist3d[0:3]:
					sock.sendall('ready?')
					try:
						response = sock.recv(16)
					except:
						print 'A player has disconnected from the 3d queue'
					if response:
						playersReady += 1
					else:
						if sock in self.socketlist3d:
							self.addrlist3d.remove(self.addrlist3d[self.socketlist3d.index(sock)])
							self.socketlist3d.remove(sock)
							print 'A player has disconnected from the 3d queue (3nd option)'
				if playersReady == 3:
					print 'a game can begin'

					tictac3dgame = threading.Thread(target=self.tictac3d,args=(self.socketlist3d[0:3],self.addrlist3d[0:3]))
					tictac3dgame.daemon = True
					tictac3dgame.start() #starts tictac3d thread

					del self.socketlist3d[0:3]
					del self.addrlist3d[0:3]
				else:
					print 'a game can not begin; player count is only %s' % str(playersReady)
					for sock in self.socketlist3d:
						sock.sendall('waiting for additional players')



	def playerqueue2d(self,s,addr):
		self.socketlist2d.append(s)
		self.addrlist2d.append(addr)
		print "2d socket list: " + str(self.socketlist2d)
		print "2d addr list: " + str(self.addrlist2d)		

		#for sock in self.socketlist2d:
		#	sock.sendall('waiting for additional players')
				
		#if len(self.socketlist2d) >= 2:
		#	for sock in self.socketlist2d[0:2]
		#	userthread = threading.Thread(target=self.tictac2d,args=(self.socketlist2d,self.addrlist2d))
		#	userthread.daemon = True
		#	userthread.start()
		#	self.socketlist2d = []
		#	self.addrlist2d = []


	def playerqueue3d(self,s,addr):
		self.socketlist3d.append(s)
		self.addrlist3d.append(addr[0])
		print "3d socket list: " + str(self.socketlist3d)
		print "3d addr list: " + str(self.addrlist3d)	

	def exit(self): #kill all proceses for a tidy exit
        self.shouldExit = True

if __name__ == '__main__':
	CommonCode_Server.main(sys.argv[1:],TemplateServer)