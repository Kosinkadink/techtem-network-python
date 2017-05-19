#!/usr/bin/python2
import sys, socket, select, os
from random import choice

# initialization of the client
__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))  # directory from which this script is ran
if os.name == 'nt':
    __location__ = __location__.replace('\\', '/')
sys.path.insert(0, os.path.join(__location__, 'resources/source/'))

# import common code
import CommonCode
import CommonCode_Client


class NetworkClient(object):
    netPass = None
    threads = []
    serverport = None
    serverports = None
    send_cache = 40960
    version = "3.0.0"

    class ClientObject(object):
        location = None
        data = None
        send_cache = None  # data send cache for non-encrypted connection
        s = None  # socket connection

        def __init__(self, s, data, send_cache, send_cache_enc, location):
            self.s = s
            self.data = data
            self.send_cache = send_cache
            self.location = location

    def __init__(self):
        self.initialize()

    def run_processes(self):
        self.serverterminal()

    def initialize(self):
        if not os.path.exists(__location__ + '/resources'): os.makedirs(__location__ + '/resources')
        if not os.path.exists(__location__ + '/resources/source'): os.makedirs(
            __location__ + '/resources/source')  # stores common code
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
        self.createFileTransferProt(__location__)
        self.netPass = self.get_netPass(__location__)
        self.gen_protlist(__location__)
        self.init_spec()
        self.run_processes()

    def injectCommonCode(self):
        CommonCode_Client.__location__ = __location__
        self.clear = CommonCode.clear
        self.connectip = CommonCode_Client.connectip_netclient
        self.get_netPass = CommonCode.get_netPass
        self.gen_protlist = CommonCode.gen_protlist
        self.netPass_check = CommonCode.netPass_check
        self.createFileTransferProt = CommonCode.createFileTransferProt

    def init_spec(self):
        # name files start
        if not os.path.exists(__location__ + '/resources/programparts/name'): os.makedirs(
            __location__ + '/resources/programparts/name')
        if not os.path.exists(__location__ + '/resources/programparts/name/nameservers.txt'):
            with open(__location__ + '/resources/programparts/name/nameservers.txt',
                      "a") as makeprot:  # file used for listing network name servers for /connect functionality
                makeprot.write("")
            # name files end

    def boot(self):
        self.clear()
        print "Welcome to the TechTem Network Client"
        print "Version %s" % self.version
        print "Type help for command list\n"

    # function for client splash screen

    def help(self):
        print "TechTem Network Client Commands:"
        print "connect + URL: retrieve address and connect"
        print "dconnect + IP: directly connect to IP"
        print "reload: creates an updated local protocol list"
        print "prots: prints out loaded prots with relevant values"
        print "exit OR leave: exits gracefully"
        print "help OR ?: displays this menu"

    def serverterminal(self):
        self.boot()
        while 1:
            inp = raw_input(">")
            try:
                if inp:
                    if inp.split()[0] == 'connect':
                        try:
                            data = inp.split()[1:]
                        except:
                            print 'connect command requires at least 1 argument; 0 provided'
                        else:
                            print self.termConnectCommand(data)

                    elif inp.split()[0] == 'dconnect':
                        try:
                            ip = inp.split()[1]
                            data = inp.split()[2:]
                        except:
                            'dconnect command requires at least 2 arguments; less provided'
                        else:
                            print self.termDconnectCommand(ip, data)
                    elif inp.split()[0] == 'start':
                        try:
                            data = inp.split()[1:]
                        except:
                            data = None
                        print self.startstandalone(data)
                    elif inp.split()[0] == 'reload':
                        self.gen_protlist()
                        print 'protocols list reloaded'
                    elif inp.split()[0] == 'prots':
                        self.printProts()
                    elif inp.split()[0] == 'quit' or inp.split()[0] == 'leave' or inp.split()[0] == 'exit':
                        self.exit()
                    elif inp.split()[0] == 'clear':
                        self.boot()
                    elif inp.split()[0] == 'help' or inp.split()[0] == '?':
                        self.help()
                    else:
                        print "Invalid command"
            except Exception, e:
                print str(e)

    def printProts(self):
        with open(__location__ + '/resources/protocols/protlist.txt') as protlist:
            for scriptname in protlist:
                if scriptname.endswith('\n'):
                    scriptname = scriptname[:-1]
                script = sys.modules[scriptname]
                try:
                    isAlone = getattr(script, 'standalone')
                except Exception, e:
                    isAlone = 'Unknown'
                try:
                    variables = getattr(script, 'variables')
                except Exception, e:
                    variables = 'Unknown'
                print '%s --> standalone=%s, input=%s' % (scriptname, str(isAlone), str(variables))

    def startstandalone(self, data):  # used to start protocols not requiring connection

        try:
            scriptname = data[0]
            compat = 'n'
            with open(__location__ + '/resources/protocols/protlist.txt') as protlist:
                for line in protlist:
                    if line == scriptname or line == scriptname + '\n':
                        compat = 'y'
                        break

            if compat == 'y':
                script = sys.modules[scriptname]
                try:
                    isAlone = getattr(script, 'standalone')
                except:
                    isAlone = False
                finally:
                    if not isAlone:
                        return 'protocol is not specified as standalone'
                varcheck = getattr(script, 'variables')
                if len(varcheck) <= len(data):
                    function = getattr(script, 'standalonefunction')
                    use = getattr(script, function)
                    print 'success'
                else:
                    print 'incorrect argument[s]'
            else:
                return 'failure - protocol not found'

            query = use(data, __location__, True)
            self.boot()
            return query
        except Exception, e:
            return str(e)

    def termConnectCommand(self, data):
        receivedip = self.makenameconnection(data)
        print receivedip
        return self.connectViaProt(receivedip, data[1:])

    def termDconnectCommand(self, ip, data):
        return self.connectViaProt(ip, data)

    def connectViaProt(self, receivedip, data):
        query = self.connectip(self, receivedip, data, 'none:none_function:1.0')
        print query
        if query.startswith('n|'):
            need = query.split('|')[1]
            downloc = query.split('|')[2]
            scriptname, function, scriptversion = need.split(':')
            compat = False
            with open(__location__ + '/resources/protocols/protlist.txt') as protlist:
                for line in protlist:
                    if line == scriptname or line == scriptname + '\n':
                        compat = True
            if not compat:
                if need != '':
                    confirm = self.confirmDownload(receivedip, need, downloc)
                    if not confirm:
                        return """Download aborted. Client requires script '%s' of version '%s' to connect to this server; client does not posses the script""" % (
                        scriptname, scriptversion)
                    print 'Download confirmed'
                    protdownload = self.downloadProt(downloc)
                    print protdownload
                    if protdownload != '111':
                        return """File not found on designated file server. Client requires script '%s' of version '%s' to connect to this server; client does not posses the script""" % (
                        scriptname, scriptversion)
                    self.gen_protlist()
                    with open(__location__ + '/resources/protocols/protlist.txt') as protlist:
                        for line in protlist:
                            if line == scriptname or line == scriptname + '\n':
                                compat = True
                    if not compat:
                        return """Client requires script '%s' of version '%s' to connect to this server; client does not posses the script""" % (
                        scriptname, scriptversion)
                else:
                    return """Client requires script '%s' of version '%s' to connect to this server; client does not posses the script""" % (
                    scriptname, scriptversion)

            script = sys.modules[scriptname]
            preversion = getattr(script, 'version')
            if preversion == scriptversion:
                return self.connectip(self, receivedip, data, '%s:%s:%s' % (scriptname, function, scriptversion))
            else:
                return """Client requires script '%s' of version '%s' to connect to this server; client has wrong version '%s'""" % (
                scriptname, scriptversion, preversion)
        else:
            return 'Communication complete'

    def downloadProt(self, downloc):
        ip, loc = downloc.split('&&')
        try:
            scriptname = 'filetransfer'
            script = sys.modules[scriptname]
            preversion = getattr(script, 'version')
            function = getattr(script, 'clientfunction')
        except:
            return '404'
        return self.connectip(self, ip, [loc + '::/resources/protocols/'],
                              '%s:%s:%s' % (scriptname, function, preversion))

    def confirmDownload(self, receivedip, need, downloc):
        confirm = raw_input(
            'Server at %s points at %s to download the nessecary protocol %s. Proceed with download?\n>> ' % (
            receivedip, downloc.split('&&')[0], need))
        if confirm.lower() == 'y':
            return True
        return False

    def makenameconnection(self, data):
        with open(__location__ + '/resources/programparts/name/nameservers.txt', "r") as nservelist:
            for line in nservelist:
                if line.startswith('||'):
                    try:
                        host = line.split('||')[1].split(':')[0]
                        port = line.split('||')[1].split(':')[1]
                        ip = '%s:%s' % (host, port)
                        scriptname = 'name'
                        script = sys.modules[scriptname]
                        function = getattr(script, 'clientfunction')
                        scriptversion = getattr(script, 'version')
                        command = '%s:%s:%s' % (scriptname, function, scriptversion)
                        return self.connectip(self, ip, data, command)
                    except Exception, e:
                        print e
            return "None of the listed name servers could be reached"

    def clear(self):  # clear screen, typical way
        if os.name == 'nt':
            os.system('cls')
        else:
            os.system('clear')

    def exit(self):
        quit()


if __name__ == '__main__':
    program = NetworkClient()
