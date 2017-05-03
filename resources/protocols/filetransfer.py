#!/usr/bin/python2
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

    #s.sendall('end\n')

def file_recv_file(filename,cliObj): #receives files from master
    
    ################################
    s = cliObj.s
    send_cache = cliObj.send_cache
    send_cache_enc = cliObj.send_cache_enc
    location = cliObj.location
    ################################
    filereq = filename.split('::')
    s.sendall(filereq[0])

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
        file_cache = s.recv(16)
        file_cache = int(file_cache.strip())
        s.sendall('ok')
        size = s.recv(16)
        size = int(size.strip())
        recvd = 0
        print filename + ' download in progress...'
        if not os.path.exists(downloadslocation):
            os.makedirs(downloadslocation)
        q = open(os.path.join(downloadslocation, filename), 'wb')
        while size > recvd:
            sys.stdout.write(str((float(recvd)/size)*100)[:4]+ '%' + '\r')
            sys.stdout.flush()
            data = s.recv(file_cache)
            if not data: 
                break
            recvd += len(data)
            q.write(data)
        s.sendall('ok')
        q.close()
        sys.stdout.write('100.0%\n')
        print filename + ' download complete'
        return '111'
