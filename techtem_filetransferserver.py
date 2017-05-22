import sys, socket, select, os, threading, getopt
from time import strftime, sleep

# initialization of the server
__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))  # directory from which this script is ran
if os.name == 'nt':
    __location__ = __location__.replace('\\', '/')
sys.path.insert(0, os.path.join(__location__, 'resources/source/'))

# import common code
import CommonCode_Server


class TemplateServer(CommonCode_Server.TemplateServer):
    # don't change this
    netPass = None
    threads = []
    startTime = None
    # change this to default values
    varDict = dict(version='3.0.0', serverport=9011, userport=10011, useConfigPort=True, send_cache=409600,
                   scriptname='filetransfer', name='filetransfer', downloadAddrIP='jedkos.com:9011',
                   downloadAddrLoc='protocols/filetransfer.py')

    def __init__(self, location, serve=varDict["serverport"], user=varDict["userport"], startUser=True):
        CommonCode_Server.TemplateServer.__init__(self, location, serve, user, startUser)
        self.funcMap = {
            'fileget': self.sendFileCommand
        }

    def init_spec_extra(self):
        self.downloadLoc = os.path.join(self.__location__, "resources/downloads")
        if not os.path.exists(self.__location__ + '/resources/programparts/filetransfer/approvedfiles.txt'):
            with open(self.__location__ + '/resources/programparts/filetransfer/approvedfiles.txt', "a") as makeprot:
                makeprot.write("")

    def sendFileCommand(self, s, data):
        # get full path of file
        file_path = os.path.join(self.downloadLoc, data["file"])
        # check if file exists
        if not os.path.exists(file_path):
            # does not exist, so tell client
            s.sendall("n")
        else:
            # exists, tell the client to receive it
            s.sendall("y")
            # get filename
            file_name = data["file"].split("/")
            # send file
            self.send_file(s, file_path, file_name, self.varDict["send_cache"])


    # def sendFile(self, s):  # send file to seed
    #
    #     fileloc = s.recv(1024)
    #     print 'searching for %s' % fileloc
    #     searchfile = __location__ + '/resources/uploads/' + fileloc
    #
    #     try:
    #         file_name = fileloc.split('/')[-1]
    #     except:
    #         file_name = fileloc
    #
    #     file = searchfile
    #
    #     if os.path.exists(file):
    #         print file_name + " found"
    #         s.sendall('ok')
    #         s.recv(2)
    #
    #         if s.getKey() == None:
    #             use_cache = self.send_cache
    #         else:
    #             use_cache = self.send_cache_enc
    #
    #         s.sendall('%16d' % use_cache)
    #         s.recv(2)
    #
    #         filelength = os.path.getsize(file)
    #         s.sendall('%16d' % filelength)
    #         with open(file, 'rb') as f:
    #             print file_name + " sending..."
    #             sent = 0
    #             while True:
    #                 try:
    #                     sys.stdout.write(str((float(sent) / filelength) * 100)[:4] + '%   ' + str(sent) + '/' + str(
    #                         filelength) + ' B\r')
    #                     sys.stdout.flush()
    #                 except:
    #                     pass
    #                 data = f.read(use_cache)
    #                 if not data:
    #                     break
    #                 sent += len(data)
    #                 s.sendall(data)
    #         s.recv(2)
    #         sys.stdout.write('100.0%   ' + str(sent) + '/' + str(filelength) + ' B\n')
    #         print file_name + " sending successful"
    #
    #     else:
    #         print file_name + " not found"
    #         s.sendall('no')
    #
    # def fileSendCommand(self, s):
    #     self.sendFile(s)
    #
    # def exit(self):  # kill all proceses for a tidy exit
    #     self.shouldExit = True


if __name__ == '__main__':
    CommonCode_Server.main(sys.argv[1:], TemplateServer, __location__)
