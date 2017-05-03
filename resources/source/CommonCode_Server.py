#!/usr/bin/python2

import socket, select, os, sys, threading, getopt
from time import sleep
import ssl

import CommonCode

__location__ = None

def distinguishCommand(self,s):
	order = s.recv(128)
	print 'command is: %s' % order

	try:
		func = self.funcMap[order]
	except KeyError:
		s.send('no')
		print 'command %s not understood' % order
	else:
		s.send('ok')
		print 'command understood, performing: %s' % order
		func(s)

def servergen(self,repeatFunc = None):
    print '%s server started - version %s on port %s\n' % (self.name,self.version,self.serverport)
    self.get_netPass(__location__)
    # create a socket object
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socketlist = []
    # get local machine name
    host = ""
    port = self.serverport

    userinput = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # bind to the port + admin port
    try:
        serversocket.bind((host, port))
        userinput.bind((host, port+1000))
    except Exception,e:
        print str(e)
        self.shouldExit = True  

    # queue up to 10 requests
    serversocket.listen(10)
    socketlist.append(serversocket)
    #start admin socket
    userinput.listen(2)
    socketlist.append(userinput)

    while 1 and not self.shouldExit:
    	if repeatFunc != None:
    		repeatFunc()
        sleep(.1)
        
        ready_to_read,ready_to_write,in_error = select.select(socketlist,[],[],0)

        for sock in ready_to_read:
            # establish a connection
            if sock == userinput:
                user,addr = userinput.accept()
                userinp = user.recv(128)
                self.serverterminal(userinp)
            elif sock == serversocket:
                s,addr = serversocket.accept()
                newthread = threading.Thread(target=handleNewConnection,args=(self,s,addr))
                newthread.daemon = True
                newthread.start()
    
    userinput.shutdown(socket.SHUT_RDWR)
    userinput.close()
    serversocket.shutdown(socket.SHUT_RDWR)
    serversocket.close()
    self.exit()

def handleNewConnection(self,s,addr):
    print("Got a connection from %s" % str(addr))
    #wrap socket with TLS, handshaking happens automatically
    s = self.context.wrap_socket(s,server_side=True)
    #wrap socket with socketTem, to send length of message first
    s = CommonCode.socketTem(s)
    try:
        if self.netPass != None:
            print "checking netpass..."
            rightPass = self.netPass_check(s,self.netPass)
            print 'done checking netpass!'
        else:
            rightPass = True
            s.sendall('np')

        if rightPass == True:
            identity = s.recv(1024)
            compat = 'n'
            scriptname,function,cli_version = identity.split(':')
            if scriptname == self.scriptname and function == self.function and cli_version == self.version:
                compat = 'y'

            s.sendall(compat)

            if compat != 'y': #not a name_client, so respond with 
                s.recv(2)
                #s.sendall('n|sync:sync_client:%s|' % version)
                s.sendall('n|%s:%s:%s|%s' % (self.scriptname,self.function,self.version,self.downloadAddrLoc))
                print 'does not have protocol'
            else:
                print 'HAS protocol'
                s.recv(2)
                s.sendall('ok')
                distinguishCommand(self,s)

            print("Disconnection by %s with data received" % str(addr))

    except Exception,e:
        print str(e) + '\n'

def socket_raw_input(port):
    admin_port = port+1000
    #connect to port
    while True:
        userinp = raw_input()
        tries = 0
        success = False
        error = None
        while tries < 5:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect(('localhost',admin_port))
            except Exception,e:
                error = e
                tries += 1
            else:
                success = True
                break
        if not success:
            raise e
        s.sendall(userinp)
        if userinp == 'exit':
            s.close()
            break

def main(argv,TemplateServer):
    startRawInput = True
    portS = None
    try:
        opts,args = getopt.getopt(argv, 'tp:',['port='])
    except getopt.GetoptError:
        print '-p [port] or --port [port] only'
        quit()
    for opt, arg in opts:
        if opt in ("-p","--port"):
            portS = arg
        if opt in ("-t"):
            startRawInput = False

    if portS == None:
        if startRawInput:
            print 'starting input thread...'
            raw_input_thread = threading.Thread(target=socket_raw_input,args=(TemplateServer.serverport,))
            raw_input_thread.daemon = True
            raw_input_thread.start()
        program = TemplateServer().start()
    else:
        try:
            portI = int(portS)
        except ValueError:
            print 'port must be an integer'
        else:
            if startRawInput:
                print 'starting input thread...'
                raw_input_thread = threading.Thread(target=socket_raw_input,args=(portI,))
                raw_input_thread.daemon = True
                raw_input_thread.start()
            program = TemplateServer(portI).start()

class TemplateServer(object):

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
    send_cache = 409600
    scriptname = None
    function = None
    name = 'template'
    downloadAddrLoc = 'jedkos.com:9011&&protocols/name.py' 
    #form is ip:port&&location/on/filetransferserver/file.py
    context = None


    def __init__(self, serve=serverport):
        if serve != None:
            self.useConfigPort = False
            self.serverport = int(serve)
        self.shouldExit = False

    def start(self):
        self.run()

    def run(self):
        self.initialize()

    def run_processes(self):
        try:
            self.servergen(self)
        except Exception,e:
            print str(e)
            self.shouldExit = True

    def initialize(self):
        # make directories if dont exist
        if not os.path.exists(__location__+'/resources'): os.makedirs(__location__+'/resources')
        if not os.path.exists(__location__+'/resources/protocols'): os.makedirs(__location__+'/resources/protocols') #for protocol scripts
        if not os.path.exists(__location__+'/resources/cache'): os.makedirs(__location__+'/resources/cache') #used to store info for protocols and client
        if not os.path.exists(__location__+'/resources/programparts'): os.makedirs(__location__+'/resources/programparts') #for storing protocol files
        if not os.path.exists(__location__+'/resources/uploads'): os.makedirs(__location__+'/resources/uploads') #used to store files for upload
        if not os.path.exists(__location__+'/resources/downloads'): os.makedirs(__location__+'/resources/downloads') #used to store downloaded files
        if not os.path.exists(__location__+'/resources/networkpass'): os.makedirs(__location__+'/resources/networkpass') #contains network passwords
        #perform all tasks
        self.injectCommonCode()
        self.netPass = self.get_netPass(__location__)
        self.gen_protlist(__location__)
        self.generateContextTLS()
        self.init_spec()
        #config stuff
        self.loadConfig()
        self.run_processes()

    def loadConfig(self):
        varDir = {'version': self.version,
        'serverport': self.serverport,
        'send_cache': self.send_cache,
        'scriptname': self.scriptname,
        'function': self.function,
        'name': self.name,
        'downloadAddrLoc': self.downloadAddrLoc}
        #load config values, or create default file
        newVarDict = self.config(varDir,__location__,self.useConfigPort)
        #reassign values
        self.version = newVarDict['version']
        self.serverport = int(newVarDict['serverport'])
        self.send_cache = int(newVarDict['send_cache'])
        self.scriptname = newVarDict['scriptname']
        self.function = newVarDict['function']
        self.name = newVarDict['name']
        self.downloadAddrLoc = newVarDict['downloadAddrLoc']

    def injectCommonCode(self):
        self.clear = CommonCode.clear
        self.servergen = servergen
        self.distinguishCommand = distinguishCommand
        self.get_netPass = CommonCode.get_netPass
        self.gen_protlist = CommonCode.gen_protlist
        self.netPass_check = CommonCode.netPass_check
        self.createFileTransferProt = CommonCode.createFileTransferProt
        self.config = CommonCode.config

    def generateContextTLS(self):
        cert_loc = os.path.join(__location__,'resources/source/certification')
        self.context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        self.context.load_cert_chain(certfile=os.path.join(cert_loc,'techtem_cert.pem'),keyfile=os.path.join(cert_loc,'techtem_server_key.pem'))
        self.context.load_verify_locations(cafile=os.path.join(cert_loc,'techtem_cert_client.pem'))
        self.context.verify_mode = ssl.CERT_REQUIRED

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

    def info(self): #display current configuration
        print "INFORMATION:"
        print "name: %s" % self.name
        print "version: %s" % self.version
        print "serverport: %s" % self.serverport
        print "send_cache: %s" % self.send_cache
        print "scriptname: %s" % self.scriptname
        print "function: %s" % self.function
        print "downloadAddrLoc: %s" % self.downloadAddrLoc
        print ""