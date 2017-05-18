#!/usr/bin/python2

import socket, select, os, sys, threading
from time import sleep
import ssl, json, ast

import CommonCode

__location__ = None


def connectip(self, ip, data, command):  # connect to ip
    try:
        host = ip.split(':')[0]
        port = int(ip.split(':')[1])
    except:
        return 'invalid host/port provided\n'
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5)
    try:
        s.connect((host, port))
    except:
        s.close()
        return "Server at " + ip + " not available\n"
    print "\nConnection successful to " + ip
    return connectprotocolclient(self, s, data, command)


def connectip_netclient(self, ip, data, command):
    try:
        host = ip.split(':')[0]
        port = int(ip.split(':')[1])
    except:
        return 'invalid host/port provided\n'
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5)
    try:
        s.connect((host, port))
    except:
        s.close()
        return "Server at " + ip + " not available\n"
    print "\nConnection successful to " + ip
    return connectprotocolclient_netclient(self, s, data, command)


def distinguishCommand(self, s, data, command):  # interpret what to tell seed
    try:
        func = self.funcMap[command]
    except KeyError:
        print 'unknown commmand: %s' % command
        s.send('no')
    else:
        s.sendall(command)
        understood = s.recv(2)
        if understood == 'ok':
            print 'command: %s understood by seed' % command
            return func(s, data)
        else:
            print 'command: %s not understood by seed' % command


def connectprotocolclient(self, s, data, command):  # communicate via protocol to command seed
    global version
    # wrap socket with TLS, handshaking happens automatically
    s = self.context.wrap_socket(s)
    # wrap socket with socketTem, to send length of message first
    s = CommonCode.socketTem(s)
    # create connection request
    conn_req = json.dumps({
        "netpass": self.get_netPass(__location__),
        "scriptname": self.scriptname,
        "scriptfunction": self.scriptfunction,
        "version": self.version,
        "command": command,
        "data": data
    })
    # check if command exists; stop connection if not
    try:
        func = self.funcMap[command]
    except KeyError, e:
        s.close()
        return {"status": 499, "msg": "client does not recognize command: %s" % command}
    # send connection request
    s.sendall(conn_req)
    # get response from server
    conn_resp = ast.literal_eval(s.recv(1024))
    # determine if good to go
    if conn_resp["status"] != 200:
        s.close()
        print "failure. closing connection: {0}:{1}".format(conn_resp["status"], conn_resp["msg"])
        return conn_resp
    else:
        print "success. continuing..."
        return func(s, data)


# #hasPass = s.recv(2)
#	#print hasPass
#	#if hasPass == 'yp':
#	#	if self.netPass == None:
#	#		s.sendall('n')
#	#		s.close()
#	#		return 'requires password'
#	#	else:
#	#		s.sendall('y')
#	#		s.recv(2)
#	#		s.sendall(self.netPass)
#	#		right = s.recv(1)
#	#		if right != 'y':
#	#			s.close()
#	#			return 'incorrect password'
#	#
#	#s.sendall('%s:%s:%s' % (self.scriptname,self.scriptfunction,self.version)) #check if sync_client is connecting
#	#compat = s.recv(1)
#	#
#	#if compat == 'y':
#	#	s.sendall('ok')
#	#	s.recv(2)
#	#	print 'success initiated'
#	#	return distinguishCommand(self, s, data, command)
#	#
#	#else:
#	#	s.sendall('ok')
#	#	#resp = s.recv(1024)
#	#	resp = s.recv(1024)
#	#	s.close()
#	#	print 'failure. closing connection...'
#	#	return resp
#
#	#s.close()
#	#return 'connection closed'


def connectprotocolclient_netclient(self, s, data, command):
    self.netPass = self.get_netPass(__location__)
    scriptname, function, scriptversion = command.split(':')
    # wrap socket with TLS, handshaking happens automatically
    s = self.context.wrap_socket(s)
    # wrap socket with socketTem, to send length of message first
    s = CommonCode.socketTem(s)
    # create connection request
    conn_req = json.dumps({
        "netpass": self.netPass,
        "scriptname": scriptname,
        "scriptfunction": function,
        "version": scriptversion,
        "command": command,
        "data": data
    })
    # send connection request
    s.sendall(conn_req)
    # get response from server
    conn_resp = ast.literal_eval(s.recv(1024))
    # determine if good to go
    if conn_resp["status"] != 200:
        s.close()
        print "failure. closing connection: {0}:{1}".format(conn_resp["status"], conn_resp["msg"])
        return conn_resp
    else:
        print "success. continuing..."
        return distinguishCommand(self, s, data, command)


# #hasPass = s.recv(2)
#	#print hasPass
#	#if hasPass == 'yp':
#	#	if self.netPass == None:
#	#		s.sendall('n')
#	#		s.close()
#	#		return 'requires password'
#	#	else:
#	#		s.sendall('y')
#	#		s.recv(2)
#	#		s.sendall(self.netPass)
#	#		right = s.recv(1)
#	#		if right != 'y':
#	#			s.close()
#	#			return 'incorrect password'
#	#
#	#s.sendall('%s:%s:%s' % (scriptname,function,scriptversion))
#	#compat = s.recv(1)
#	#
#	#if compat == 'y':
#	#	s.sendall('ok')
#	#	s.recv(2)
#	#	print 'success initiated'
#	#	script = sys.modules[scriptname]
#	#	varcheck = getattr(script,'variables')
#	#	if len(varcheck) <= len(data):
#	#		use = getattr(script,function)
#	#		keyinfo = self.ClientObject(s,data,self.send_cache,self.send_cache_enc,__location__)
#	#		return use(keyinfo)
#	#
#	#else:
#	#	s.sendall('ok')
#	#	resp = s.recv(1024)
#	#	s.close()
#	#	print 'failure. closing connection...'
#	#	return resp
#	#
#	#s.close()
#	#return 'connection closed'

# sort of an abstract class; will not work on its own
class TemplateProt(object):
    netPass = None
    password = None
    username = None
    send_cache = 409600
    send_cache_enc = 40960
    shouldEncrypt = True
    startTerminal = True
    scriptname = 'template'
    scriptfunction = 'template_client'
    version = '3.0.0'
    threads = []
    context = None

    def __init__(self, location, startTerminal):
        global __location__
        __location__ = location
        self.startTerminal = startTerminal
        self.funcMap = {}  # fill with string:functions pairs
        self.initialize()

    def run_processes(self):
        if self.startTerminal:
            # now do server terminal
            self.serverterminal()

    def initialize(self):
        if not os.path.exists(__location__ + '/resources'): os.makedirs(__location__ + '/resources')
        if not os.path.exists(__location__ + '/resources/protocols'): os.makedirs(
            __location__ + '/resources/protocols')  # for protocol scripts
        if not os.path.exists(__location__ + '/resources/cache'): os.makedirs(
            __location__ + '/resources/cache')  # used to store info for protocols and client
        if not os.path.exists(__location__ + '/resources/programparts'): os.makedirs(
            __location__ + '/resources/programparts')  # for storing protocol files
        if not os.path.exists(__location__ + '/resources/uploads'): os.makedirs(
            __location__ + '/resources/uploads')  # used to store files for upload
        if not os.path.exists(__location__ + '/resources/downloads'): os.makedirs(
            __location__ + '/resources/downloads')  # used to store downloaded files
        if not os.path.exists(__location__ + '/resources/networkpass'): os.makedirs(
            __location__ + '/resources/networkpass')  # contains network passwords
        self.injectCommonCode()
        self.netPass = self.get_netPass(__location__)
        self.gen_protlist(__location__)
        self.generateContextTLS()
        self.init_spec()
        self.run_processes()

    def injectCommonCode(self):
        self.clear = CommonCode.clear
        self.connectip = connectip
        self.distinguishCommand = distinguishCommand
        self.get_netPass = CommonCode.get_netPass
        self.gen_protlist = CommonCode.gen_protlist
        self.netPass_check = CommonCode.netPass_check
        self.createFileTransferProt = CommonCode.createFileTransferProt

    def generateContextTLS(self):
        cert_loc = os.path.join(__location__, 'resources/source/certification')
        self.context = ssl.create_default_context()
        self.context.load_cert_chain(certfile=os.path.join(cert_loc, 'techtem_cert_client.pem'),
                                     keyfile=os.path.join(cert_loc, 'techtem_client_key.pem'))
        self.context.check_hostname = False
        self.context.load_verify_locations(cafile=os.path.join(cert_loc, 'techtem_cert.pem'))

    def init_spec(self):
        # token files start
        if not os.path.exists(__location__ + '/resources/programparts/%s' % scriptname): os.makedirs(
            __location__ + '/resources/programparts/%s' % scriptname)

        if not os.path.exists(__location__ + '/resources/programparts/%s/serverlist.txt' % scriptname):
            with open(__location__ + '/resources/programparts/%s/serverlist.txt' % scriptname, "a") as seeds:
                seeds.write("""####################################################
##The format is: ||ip:port||
##Files will be sent to and from these servers
##Only lines starting with || will be read
####################################################""")
                # token files end

    def boot(self):
        self.clear()
        print "TechTem Token Client started"
        print "Version " + self.version
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
                    else:
                        print "Invalid command"
            except Exception, e:
                print str(e)

    def exit(self):
        quit()
