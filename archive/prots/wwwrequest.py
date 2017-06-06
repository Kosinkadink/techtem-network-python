#!/usr/bin/python2
import socket, os, sys
from time import sleep

variables = ['website']
standalone = False
version = '3.0.0'
clientfunction = 'wwwrequest_client'
serverfunction = None

def initialize(location):
    if not os.path.exists(location + '/resources/downloads/wwwrequest'):
        os.makedirs(location + '/resources/downloads/wwwrequest') #used to store HTML files

def wwwrequest_client(cliObj):

    ################################
    s = cliObj.s
    send_cache = cliObj.send_cache
    send_cache_enc = cliObj.send_cache_enc
    location = cliObj.location
    data = cliObj.data
    ################################
    initialize(location)
    filename = data[0]
    command = 'request'
    s.sendall(command)
    understood = s.recv(2)
    if understood != "ok":
        return "command %s not understood by server" % command

    s.sendall(filename)
    resp = s.recv(2)
    if resp != 'ok':
        print "server says no"
        return '404\n'
    status = web_recv_file(cliObj,filename)
    s.close
    return status

def web_recv_file(cliObj,filename): #receives files from master

    ################################
    s = cliObj.s
    send_cache = cliObj.send_cache
    send_cache_enc = cliObj.send_cache_enc
    location = cliObj.location
    ################################

    downloadslocation = location + '/resources/downloads/wwwrequest/' 

    newname = ''
    skippedchars = '/.:!@#$%^&*()<>=+?,|\\"'
    for character in filename:
        if character not in skippedchars:
            newname += character
    newname += '.html'

    s.sendall('ok')
    file_cache = s.recv(16)
    file_cache = int(file_cache.strip())
    s.sendall('ok')
    size = s.recv(16)
    size = int(size.strip())
    recvd = 0
    print newname + ' download in progress...'
    if not os.path.exists(downloadslocation):
        os.makedirs(downloadslocation)
    q = open(os.path.join(downloadslocation, newname), 'wb')
    while size > recvd:
        sys.stdout.write(str((float(recvd)/size)*100)[:4]+ '%   ' + str(recvd) + '/' + str(size) + ' B\r')
        sys.stdout.flush()
        data = s.recv(file_cache)
        if not data: 
            break
        recvd += len(data)
        q.write(data)
    s.sendall('ok')
    q.close()
    sys.stdout.write('100.0%   ' + str(recvd) + '/' + str(size) + ' B\n')
    print newname + ' download complete'
    return '111'
