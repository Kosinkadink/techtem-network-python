#!/usr/bin/python2
import socket, os, sys
from time import sleep

common_location = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))  # directory from which this script is ran
main_dir = os.path.realpath(os.path.join(common_location, '..'))
sys.path.insert(0, os.path.join(main_dir, 'source/'))
import CommonCode_Client

# variables = ['filename']
# standalone = False
# version = '3.0.0'
# clientfunction = 'filetransfer_client'
# serverfunction = None


class TemplateProt(CommonCode_Client.TemplateProt):
    standalone = False
    default_vars = ["file_request"]
    default_command = "getname"
    varDict = dict(send_cache=409600, scriptname='filetransfer', version='3.0.0')

    def __init__(self, location, startTerminal):
        CommonCode_Client.TemplateProt.__init__(self, location, startTerminal)

    def set_funcMap(self):
        self.add_to_funcMap("fileget", self.getFileCommand)

    def set_terminalMap(self):
        self.terminalMap["getfile"] = (lambda data: self.makeFileDownloadConnection(data[1:]))

    def process_list_to_dict(self, input_list):
        """
        Transform a list of strings into proper dictionary output to be sent to server
        :param input_list: list containing files requested
        :return: dictionary to use as data
        """
        return {"file": input_list[0]}

    def getFileCommand(self, s, data, dataToSave):
        if dataToSave["saveloc"] is None:
            dataToSave["saveloc"] = "resources/downloads/"
        # find out if file exists
        exists = s.recv(1)
        if exists != "y":
            return {"status": 404, "msg": "file does not exist"}
        else:
            downloadsLocation = os.path.join(dataToSave["saveloc"], dataToSave["file_name"])
            # download requested file
            return self.recv_file(s, downloadsLocation, dataToSave["file_name"], self.varDict["send_cache"])

    def makeFileDownloadConnection(self, ip, files_to_get, saveLoc = None):
        # if argument is string, convert to list
        if isinstance(files_to_get,type("")):
            files_to_get = [files_to_get]
        dataToKeep = {"saveloc": saveLoc}
        return self.connectip(ip, self.process_list_to_dict(files_to_get), "fileget", dataToStore=dataToKeep)
#
# def filetransfer_client(cliObj):
#     s = cliObj.s
#     data = cliObj.data
#
#     s.send('fileget')
#     s.recv(2)
#     filename = data[0]
#
#     status = file_recv_file(filename, cliObj)
#     s.close
#     return status
#
#     # s.sendall('end\n')
#
#
# def file_recv_file(filename, cliObj):  # receives files from master
#
#     ################################
#     s = cliObj.s
#     send_cache = cliObj.send_cache
#     send_cache_enc = cliObj.send_cache_enc
#     location = cliObj.location
#     ################################
#     filereq = filename.split('::')
#     s.sendall(filereq[0])
#
#     if len(filereq) > 1:
#         downloadslocation = filereq[1]
#     else:
#         downloadslocation = '/resources/downloads/'
#     downloadslocation = location + downloadslocation
#
#     filename = filereq[0].split('/')[-1]
#     print filename
#
#     has = s.recv(2)
#     if has != 'ok':
#         return '404'
#     else:
#         s.sendall('ok')
#         file_cache = s.recv(16)
#         file_cache = int(file_cache.strip())
#         s.sendall('ok')
#         size = s.recv(16)
#         size = int(size.strip())
#         recvd = 0
#         print filename + ' download in progress...'
#         if not os.path.exists(downloadslocation):
#             os.makedirs(downloadslocation)
#         q = open(os.path.join(downloadslocation, filename), 'wb')
#         while size > recvd:
#             sys.stdout.write(str((float(recvd) / size) * 100)[:4] + '%' + '\r')
#             sys.stdout.flush()
#             data = s.recv(file_cache)
#             if not data:
#                 break
#             recvd += len(data)
#             q.write(data)
#         s.sendall('ok')
#         q.close()
#         sys.stdout.write('100.0%\n')
#         print filename + ' download complete'
#         return '111'
