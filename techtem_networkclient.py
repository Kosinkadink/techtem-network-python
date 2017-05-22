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
        with open(__location__ + '/resources/protocols/protlist.txt') as protlist:
            for scriptname in protlist:
                if scriptname.endswith('\n'):
                    scriptname = scriptname[:-1]
                script = sys.modules[scriptname]
                try:
                    isAlone = getattr(script.TemplateProt, 'standalone')
                except Exception, e:
                    isAlone = 'Unknown'
                try:
                    variables = getattr(script.TemplateProt, 'default_vars')
                except Exception, e:
                    variables = 'Unknown'
                print '%s --> standalone=%s, input=%s' % (scriptname, str(isAlone), str(variables))

    def startStandalone(self, data):  # used to start protocols not requiring connection

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

    def makenameconnecton(self, data):
        nameservers = self.parse_settings_file(os.path.join(__location__ ,'resources/programparts/name/nameservers.txt'))

    # def makenameconnection(self, data):
    #     with open(__location__ + '/resources/programparts/name/nameservers.txt', "r") as nservelist:
    #         for line in nservelist:
    #             if line.startswith('||'):
    #                 try:
    #                     host = line.split('||')[1].split(':')[0]
    #                     port = line.split('||')[1].split(':')[1]
    #                     ip = '%s:%s' % (host, port)
    #                     scriptname = 'name'
    #                     script = sys.modules[scriptname]
    #                     function = getattr(script, 'clientfunction')
    #                     scriptversion = getattr(script, 'version')
    #                     command = '%s:%s:%s' % (scriptname, function, scriptversion)
    #                     return self.connectip(self, ip, data, command)
    #                 except Exception, e:
    #                     print e
    #         return "None of the listed name servers could be reached"

    def clear(self):  # clear screen, typical way
        if os.name == 'nt':
            os.system('cls')
        else:
            os.system('clear')

    def exit(self):
        quit()


if __name__ == '__main__':
    program = NetworkClient(__location__)
