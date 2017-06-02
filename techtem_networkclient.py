#!/usr/bin/python2
import sys, socket, select, os
from random import choice

# initialization of the client
__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))  # directory from which this script is ran
if os.name == 'nt':
    __location__ = __location__.replace('\\', '/')

# import common code
import resources.source.CommonCode_Client as CommonCode_Client


class NetworkClient(CommonCode_Client.TemplateProt):
    netPass = None
    threads = []
    serverport = None
    serverports = None
    varDict = dict(send_cache=409600, scriptname='network_client', version='3.0.0')

    def __init__(self, location, startTerminal=True):
        CommonCode_Client.TemplateProt.__init__(self, location, startTerminal)

    def set_terminalMap(self):
        self.terminalMap = {"exit": (lambda data: self.exit()), "clear": (lambda data: self.boot()),
                            "connect": (lambda data: self.termConnectCommand(data[1:])),
                            "dconnect": (lambda data: self.termDconnectCommand(data[1], data[2:])),
                            "start": (lambda data: self.startStandalone(data[1])),
                            "prots": (lambda data: self.printProts()),
                            "help": (lambda data: self.help())}

    def boot(self):
        self.clear()
        print "Welcome to the TechTem Network Client"
        print "Version %s" % self.varDict["version"]
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

    def printProts(self):
        protlist = self.protocolManager.get_available_list()
        for scriptname in protlist:
            script = self.protocolManager.get_protocol(scriptname)
            # check if protocol is imported
            if script is None:
                print "{} --> not imported"
            else:
                try:
                    isAlone = getattr(script.TemplateProt, 'standalone')
                except Exception, e:
                    isAlone = 'Unknown'
                try:
                    variables = getattr(script.TemplateProt, 'default_vars')
                except Exception, e:
                    variables = 'Unknown'
                print '{} --> standalone={}, input={}'.format(scriptname, str(isAlone), str(variables))

    def startStandalone(self, scriptname):  # used to start protocols not requiring connection
        script = self.protocolManager.get_protocol(scriptname)
        # check if protocol is imported
        try:
            if script is None:
                print "ERROR: {} is not imported or does not exist".format(scriptname)
            else:
                try:
                    isAlone = getattr(script.TemplateProt, 'standalone')
                except:
                    isAlone = False
                finally:
                    if not isAlone:
                        print "ERROR: {} is not specified as standalone".format(scriptname)
                        return None
                prot = script.TemplateProt
                print("success loading {}".format(scriptname))
                # run protocol
                prot(self.__location__, startTerminal=True)
                self.boot()
                print("Left {} client, back in main client.".format(scriptname))
                return None
        except Exception, e:
            print("ERROR: {}".format(str(e)))
            return None

    def loadStandalone(self, scriptname):
        pass

    def unloadStandalone(self, scriptname):
        pass

    def termConnectCommand(self, data):
        receivedip = self.getIPFromName(data[0])
        print receivedip
        return self.connectViaProt(receivedip, data[1:])

    def termDconnectCommand(self, ip, data):
        return self.connectViaProt(ip, data)

    def connectViaProt(self, receivedip, data):
        query = self.connect_with_null_dict(receivedip)
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
            'Server at %s points at %s to download the necessary protocol %s. Proceed with download?\n>> ' % (
                receivedip, downloc.split('&&')[0], need))
        if confirm.lower() == 'y':
            return True
        return False

    def getIPFromName(self, name):
        # load protocol and make name request
        return self.protocolManager.load_protocol("name", self.__location__).makeNameConnection(name)

if __name__ == '__main__':
    program = NetworkClient(__location__)
