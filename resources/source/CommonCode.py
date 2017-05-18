#!/usr/bin/python2

import socket, select, os, sys, threading
from time import sleep
import ssl

__location__ = None


class socketTem(object):
    s = None

    def __init__(self,s):
        self.s = s

    def send(self,msg):
        total_size = '%16d' % len(msg)
        self.s.sendall(total_size + msg)

    def sendall(self,msg):
        return self.send(msg)

    def recv(self,bytes):
        timeoutSec = 5

        size_to_recv = self.s.recv(16)
        size_to_recv = int(size_to_recv.strip())

        amount = bytes
        if size_to_recv < amount:
            amount = size_to_recv
        recvd = 0
        text = ""
        while recvd < amount:
            part = self.s.recv(amount)
            recvd += len(part)
            text += part
            if part == "":
                break
        return text

    def getSocket(self):
        return self.s

    def close(self):
        self.s.close()

def selectTem(read_list,write_list,error_list,timeout):
        read_dict = {}
        write_dict = {}
        error_dict = {}
        #fill out dicts with socket:socketTem pairs
        for sTem in read_list:
            read_dict.setdefault(sTem.getSocket(),sTem)
        for sTem in write_list:
            write_dict.setdefault(sTem.getSocket(),sTem)
        for sTem in error_list:
            error_dict.setdefault(sTem.getSocket(),sTem)

        ready_to_read,ready_to_write,in_error = select.select(read_dict.keys(),write_dict.keys(),error_dict.keys(),timeout)
        #lists returned back
        ready_read = []
        ready_write = []
        have_error = []
        #fill out lists with corresponding socketTems
        for sock in ready_to_read:
            ready_read.append(read_dict[sock])
        for sock in ready_to_write:
            ready_write.append(write_dict[sock])
        for sock in in_error:
            have_error.append(error_dict[sock])

        return ready_read,ready_write,have_error

def clear(): #clear screen, typical way
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')

def gen_protlist(__location__):
    #file used for identifying what protocols are available
    #delete contents of file
    with open(__location__+'/resources/protocols/protlist.txt', "w") as protlist:
        #fill it up with relevvant protocols
        for file in os.listdir(__location__+'/resources/protocols/'):
            if file.endswith('.py'):
                prot = file[:-3]
                filename = __location__ + '/resources/protocols/' + prot + '.py'
                directory, module_name = os.path.split(filename)
                module_name = os.path.splitext(module_name)[0]

                path = list(sys.path)
                sys.path.insert(0,directory)
                try:
                    module = __import__(module_name) #cool import command
                except Exception,e:
                    raise e
                else:
                    #write prot into file if successful import
                    protlist.write(prot + '\n')
                finally:
                    sys.path[:] = path
                
def get_netPass(__location__):
    if not os.path.exists(__location__+'/resources/networkpass/default.txt'):
        with open(__location__+'/resources/networkpass/default.txt', "a") as protlist: #file used for identifying what protocols are available
            pass
        netPass = None
    else:
        with open(__location__+'/resources/networkpass/default.txt', "r") as protlist: #file used for identifying what protocols are available
            netpassword = protlist.readline().strip()
        if netpassword != '':
            netPass = netpassword
        else:
            netPass = None
    return netPass

##NETWORKING CODE
def netPass_check(s,netPass):
    s.sendall('yp')
    has = s.recv(1)
    s.sendall('ok')
    if has != 'y':
        print "does not have proper password"
        s.close
        return False
    else:
        cliPass = s.recv(512).strip()
        if cliPass != netPass:
            s.sendall('n')
            print "does not have proper password"
            s.close
            return False
        else:
            s.sendall('y')
            return True

def config(varDic,__location__):
    # if config file does not exist, create one and insert default values.
    # if config files does exist, read values from it
    name = varDic['name']
    if varDic['useConfigPort'] != None:
        usePort = varDic['useConfigPort']
    else:
        userPort = False

    if not os.path.exists(__location__+'/resources/programparts/'+name+'/config.txt'): 
        with open(__location__+'/resources/programparts/'+name+'/config.txt', "wb") as configs:
            for key,value in varDic.iteritems():
                configs.write('{0}={1}\n'.format(key,value))
    else:
        oldPort = varDic['serverport']
        with open(__location__+'/resources/programparts/'+name+'/config.txt', "r") as configs:
            for line in configs:
                try:
                    args = line.split('=')
                except:
                    pass
                try:
                    key = args[0].strip()
                    value = args[1].strip()
                    varDic[key] = value
                except Exception,e:
                    print 'Warning in config: %s' % str(e)

        #if doesnt want to use config port, set old one
        if not usePort:
            varDic['serverport'] = oldPort

    return varDic


##AUTO FILE TRANSFER
def createFileTransferProt(__location__):
    if not os.path.exists(__location__+'/resources/protocols/filetransfer.py'):
        with open(__location__+'/resources/protocols/filetransfer.py', "wb") as makeprot:
            makeprot.write("""#!/usr/bin/python2
import socket, os, sys
from time import sleep

variables = ['filename']
standalone = False
version = '3.0.0'
clientfunction = 'filetransfer_client'
serverfunction = None

def filetransfer_client(cliObj):

    s = cliObj.s
    data = cliObj.data

    s.send('fileget')
    s.recv(2)
    filename = data[0]
    
    status = file_recv_file(filename,cliObj)
    s.close
    return status

    #s.sendall('end\\n')

def file_recv_file(filename,cliObj): #receives files from master
    
    ################################
    s = cliObj.s
    sendTem = cliObj.sendTem
    recvTem = cliObj.recvTem
    AESkey = cliObj.AESkey
    send_cache = cliObj.send_cache
    send_cache_enc = cliObj.send_cache_enc
    location = cliObj.location
    ################################
    filereq = filename.split('::')
    sendTem(s,filereq[0],AESkey)

    if len(filereq) > 1:
        downloadslocation = filereq[1]
    else:
        downloadslocation = '/resources/downloads/'
    downloadslocation = location + downloadslocation

    filename = filereq[0].split('/')[-1]
    print filename

    has = s.recv(2)
    if has != 'ok':
        return '404'
    else:
        s.sendall('ok')
        file_cache = recvTem(s,16,AESkey)
        file_cache = int(file_cache.strip())
        s.sendall('ok')
        size = recvTem(s,16,AESkey)
        size = int(size.strip())
        recvd = 0
        print filename + ' download in progress...'
        if not os.path.exists(downloadslocation):
            os.makedirs(downloadslocation)
        q = open(os.path.join(downloadslocation, filename), 'wb')
        while size > recvd:
            sys.stdout.write(str((float(recvd)/size)*100)[:4]+ '%' + '\\r')
            sys.stdout.flush()
            data = recvTem(s,file_cache,AESkey)
            if not data: 
                break
            recvd += len(data)
            q.write(data)
        s.sendall('ok')
        q.close()
        sys.stdout.write('100.0%\\n')
        print filename + ' download complete'
        return '111'
        """)
