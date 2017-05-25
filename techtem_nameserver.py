import sys, json, socket, select, os, threading, getopt
from time import strftime, sleep

# initialization of the server
__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))  # directory from which this script is ran
if os.name == 'nt':
    __location__ = __location__.replace('\\', '/')

# import common code
import resources.source.CommonCode_Server as CommonCode_Server


class TemplateServer(CommonCode_Server.TemplateServer):
    # don't change this
    netPass = None
    threads = []
    # change this to default values
    varDict = dict(version='3.0.0', serverport=9010, userport=10010, useConfigPort=True, send_cache=409600,
                   scriptname='name', name='name', downloadAddrIP='jedkos.com:9011',
                   downloadAddrLoc='protocols/name.py')

    def __init__(self, location, serve=varDict["serverport"], user=varDict["userport"], startUser=True):
        CommonCode_Server.TemplateServer.__init__(self, location, serve, user, startUser)
        self.funcMap = {
            'getname': self.getNameCommand
        }

    def init_spec_extra(self):
        if not os.path.exists(__location__ + '/resources/programparts/%s/techtemurls.txt' % self.varDict["name"]):
            with open(__location__ + '/resources/programparts/%s/techtemurls.txt' % self.varDict["name"], 'wb') as urls:
                urls.write('## list name to ip in this format: name|ip:port')
        self.nameDict = self.read_name_file()

    def read_name_file(self):
        namelist = self.parse_settings_file(
            os.path.join(__location__, 'resources/programparts/%s/techtemurls.txt' % self.varDict["name"]))
        nameDict = {}
        for combo in namelist:
            nameDict[combo[0]] = combo[1]
        print nameDict
        return nameDict

    def getNameCommand(self, s, data):
        try:
            ip = self.nameDict[data["namereq"]]
        except KeyError,e:
            s.sendall(json.dumps({"status": 404, "msg":"name {} does not exist".format(data["namereq"])}))
        else:
            s.sendall(json.dumps({"status": 200, "msg": ip}))

if __name__ == '__main__':
    CommonCode_Server.main(sys.argv[1:], TemplateServer, __location__)
