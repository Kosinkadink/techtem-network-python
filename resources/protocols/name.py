import os, sys, ast

common_location = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))  # directory from which this script is ran
main_dir = os.path.realpath(os.path.join(common_location, '..'))
sys.path.insert(0, os.path.join(main_dir, 'source/'))
import CommonCode_Client


class TemplateProt(CommonCode_Client.TemplateProt):
    standalone = False
    default_vars = ["url"]
    default_command = "getname"
    varDict = dict(send_cache=409600, scriptname='name', version='3.0.0')

    def __init__(self, location, startTerminal):
        CommonCode_Client.TemplateProt.__init__(self, location, startTerminal)

    def set_funcMap(self):
        self.add_to_funcMap("getname", self.getNameCommand)

    def init_spec_extra(self):
        if not os.path.exists(self.__location__ + '/resources/programparts/%s/nameservers.txt' % self.varDict["scriptname"]):
            with open(self.__location__ + '/resources/programparts/%s/nameservers.txt' % self.varDict["scriptname"],
                      "a") as makeprot:  # file used for listing network name servers for /connect functionality
                makeprot.write("")

    def getNameCommand(self, s, data=None, dataToSave=None):
        return ast.literal_eval(s.recv(128))

# def name_function(cliObj):
#     s = cliObj.s
#     data = cliObj.data
#
#     s.sendall('name')
#     s.recv(2)
#     url = data[0]
#
#     rqst = str(url)
#     print 'requesting ip'
#     s.sendall(rqst)
#     has = s.recv(1)
#     s.sendall('ok')
#     # get message
#     ip = s.recv(1024)
#     return ip
