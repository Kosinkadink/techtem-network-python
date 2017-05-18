#!/usr/bin/python2

import socket, select, os, sys, threading, getopt
from time import sleep
import ssl, json, ast

import CommonCode

__location__ = None



def main(argv, templateServer):
    startRawInput = True
    portS = None
    try:
        opts, args = getopt.getopt(argv, 'tp:', ['port='])
    except getopt.GetoptError:
        print '-p [port] or --port [port] only'
        quit()
    for opt, arg in opts:
        if opt in ("-p", "--port"):
            portS = arg
        if opt in ("-t"):
            startRawInput = False

    if portS is None:
        templateServer(startUser=startRawInput).start()
    else:
        try:
            portI = int(portS)
        except ValueError:
            print 'port must be an integer'
        else:
            templateServer(portI, startUser=startRawInput).start()


class TemplateServer(object):
    # don't change this
    threads = []
    pipes = []
    startTime = None
    context = None
    # change this to default values
    varDict = dict(version='3.0.0', serverport=9999, userport=10999, useConfigPort=True, send_cache=409600,
                   scriptname=None, function=None, name='template',
                   downloadAddrLoc='jedkos.com:9011&&protocols/name.py')
    # form is ip:port&&location/on/filetransferserver/file.py

    def __init__(self, serve=varDict["serverport"], user=varDict["userport"], startUser=True):
        if serve is not None:
            self.varDict["useConfigPort"] = False
            self.varDict["serverport"] = int(serve)
        self.startUser = startUser
        self.shouldExit = False
        self.funcMap = {}  # fill in with a string key and a function value

    def start(self):
        self.run()

    def run(self):
        self.initialize()

    def run_processes(self):
        try:
            self.start_user_input()
            self.servergen()
        except Exception, e:
            print str(e)
            self.shouldExit = True

    def start_user_input(self):
        if self.startUser:
            raw_input_thread = threading.Thread(target=self.socket_raw_input, args=(self.varDict["userport"],))
            raw_input_thread.daemon = True
            raw_input_thread.start()
            print("user input thread started - port {}".format(self.varDict["userport"]))

    def socket_raw_input(self, admin_port):
        # connect to port
        while True:
            userinp = raw_input()
            tries = 0
            success = False
            error = None
            while tries < 5:
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.connect(('localhost', admin_port))
                except Exception, e:
                    error = e
                    tries += 1
                else:
                    success = True
                    break
            if not success:
                raise error
            s.sendall(userinp)
            if userinp == 'exit':
                s.close()
                break

    def initialize(self):
        # make directories if don't exist
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
        # perform all tasks
        self.injectCommonCode()
        self.gen_protlist(__location__)
        self.generateContextTLS()
        self.init_spec()
        # config stuff
        self.loadConfig()
        self.run_processes()

    def loadConfig(self):
        # load config values, or create default file
        self.varDict = self.config(self.varDict, __location__)
        # reassign values
        self.varDict["serverport"] = int(self.varDict["serverport"])
        self.varDict["userport"] = int(self.varDict["userport"])
        self.varDict["send_cache"] = int(self.varDict["send_cache"])

    def injectCommonCode(self):
        self.clear = CommonCode.clear
        self.get_netPass = CommonCode.get_netPass
        self.gen_protlist = CommonCode.gen_protlist
        self.netPass_check = CommonCode.netPass_check
        self.createFileTransferProt = CommonCode.createFileTransferProt
        self.config = CommonCode.config

    def generateContextTLS(self):
        cert_loc = os.path.join(__location__, 'resources/source/certification')
        self.context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        self.context.load_cert_chain(certfile=os.path.join(cert_loc, 'techtem_cert.pem'),
                                     keyfile=os.path.join(cert_loc, 'techtem_server_key.pem'))
        self.context.load_verify_locations(cafile=os.path.join(cert_loc, 'techtem_cert_client.pem'))
        self.context.verify_mode = ssl.CERT_REQUIRED

    def init_spec(self):
        # insert application-specific initialization code here
        if not os.path.exists(__location__ + '/resources/programparts/%s' % self.varDict["name"]):
            os.makedirs(__location__ + '/resources/programparts/%s' % self.varDict["name"])

    def serverterminal(self, inp):  # used for server commands
        if inp:
            if inp == 'exit':
                self.exit()
            elif inp == 'clear':
                self.clear()
            elif inp == 'info':
                self.info()

    def exit(self):  # kill all processes for a tidy exit
        self.shouldExit = True

    def info(self):  # display current configuration
        print("INFORMATION:")
        print("name: %s" % self.varDict["name"])
        print("version: %s" % self.varDict["version"])
        print("serverport: %s" % self.varDict["serverport"])
        print("userport: %s" % self.varDict["userport"])
        print("send_cache: %s" % self.varDict["send_cache"])
        print("scriptname: %s" % self.varDict["scriptname"])
        print("scriptfunction: %s" % self.varDict["scriptfunction"])
        print("downloadAddrLoc: %s" % self.varDict["downloadAddrLoc"])
        print("")

    def servergen(self, repeatFunc=None):
        print '%s server started - version %s on port %s\n' % (
            self.varDict["name"], self.varDict["version"], self.varDict["serverport"])
        self.get_netPass(__location__)
        # create a socket object
        serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socketlist = []
        # get local machine name
        host = ""
        port = self.varDict["serverport"]
        userport = self.varDict["userport"]

        userinput = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # bind to the port + admin port
        try:
            serversocket.bind((host, port))
            userinput.bind((host, userport))
        except Exception, e:
            print str(e)
            self.shouldExit = True

        # queue up to 10 requests
        serversocket.listen(10)
        socketlist.append(serversocket)
        # start admin socket
        userinput.listen(2)
        socketlist.append(userinput)

        while 1 and not self.shouldExit:
            if repeatFunc is not None:
                repeatFunc()
            sleep(.1)

            ready_to_read, ready_to_write, in_error = select.select(socketlist, [], [], 0)

            for sock in ready_to_read:
                # establish a connection
                if sock == userinput:
                    user, addr = userinput.accept()
                    userinp = user.recv(128)
                    self.serverterminal(userinp)
                elif sock == serversocket:
                    s, addr = serversocket.accept()
                    newthread = threading.Thread(target=self.handleNewConnection, args=(s, addr))
                    newthread.daemon = True
                    newthread.start()

        userinput.shutdown(socket.SHUT_RDWR)
        userinput.close()
        serversocket.shutdown(socket.SHUT_RDWR)
        serversocket.close()
        self.exit()

    def handleNewConnection(self, s, addr):
        print("Got a connection from %s" % str(addr))
        # wrap socket with TLS, handshaking happens automatically
        s = self.context.wrap_socket(s, server_side=True)
        # wrap socket with socketTem, to send length of message first
        s = CommonCode.socketTem(s)
        # receive connection request
        conn_req = ast.literal_eval(s.recv(1024))
        # determine if good to go
        readyToGo = True
        responses = {"status": 200, "msg": "OK"}
        # check netpass
        if conn_req["netpass"] != self.get_netPass(__location__):
            readyToGo = False
            responses.setdefault("errors", []).append("invalid netpass")
        # check script info
        if conn_req["scriptname"] != self.varDict["scriptname"]:
            readyToGo = False
            responses.setdefault("errors", []).append("invalid scriptname")
        if conn_req["scriptfunction"] != self.varDict["scriptfunction"]:
            readyToGo = False
            responses.setdefault("errors", []).append("invalid scriptfunction")
        if conn_req["version"] != self.varDict["version"]:
            readyToGo = False
            responses.setdefault("errors", []).append("invalid version")
        try:
            func = self.funcMap[conn_req["command"]]
        except KeyError, e:
            readyToGo = False
            responses.setdefault("errors", []).append("command not recognized: %s" % conn_req["command"])
        # if ready to go, send confirmation and continue
        if readyToGo:
            conn_resp = json.dumps(responses)
            s.sendall(conn_resp)
            func(s)
        # otherwise send info back
        else:
            responses["status"] = 400
            responses["msg"] = "BAD"
            responses["downloadAddrLoc"] = self.varDict["downloadAddrLoc"]
            conn_resp = json.dumps(responses)
            s.sendall(conn_resp)

