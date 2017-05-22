#!/usr/bin/python2

import socket, select, os, sys, threading
from time import sleep
import ssl

__location__ = None


class socketTem(object):
    s = None

    def __init__(self, s):
        self.s = s

    def send(self, msg):
        total_size = '%16d' % len(msg)
        self.s.sendall(total_size + msg)

    def sendall(self, msg):
        return self.send(msg)

    def recv(self, bytes):
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


def selectTem(read_list, write_list, error_list, timeout):
    read_dict = {}
    write_dict = {}
    error_dict = {}
    # fill out dicts with socket:socketTem pairs
    for sTem in read_list:
        read_dict.setdefault(sTem.getSocket(), sTem)
    for sTem in write_list:
        write_dict.setdefault(sTem.getSocket(), sTem)
    for sTem in error_list:
        error_dict.setdefault(sTem.getSocket(), sTem)

    ready_to_read, ready_to_write, in_error = select.select(read_dict.keys(), write_dict.keys(), error_dict.keys(),
                                                            timeout)
    # lists returned back
    ready_read = []
    ready_write = []
    have_error = []
    # fill out lists with corresponding socketTems
    for sock in ready_to_read:
        ready_read.append(read_dict[sock])
    for sock in ready_to_write:
        ready_write.append(write_dict[sock])
    for sock in in_error:
        have_error.append(error_dict[sock])

    return ready_read, ready_write, have_error


def normalize_path(path):
    if os.name == 'nt':
        path = path.replace('\\', '/')
    return path


def parse_settings_file(location):
    parsed = []
    with open(location, "rb") as settings:
        for line in settings:
            if not line.startswith("#"):
                parsed.append(line.strip().split('|'))
    return parsed


def clear():  # clear screen, typical way
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')


def recv_file(s, file_path, file_name, send_cache):
    # get size of file
    file_length = int(s.recv(16).strip())

    with open(file_path, 'wb') as f:
        print("{} receiving...".format(file_name))
        received = 0
        while file_length > received:
            # print progress of download, ignore if cannot display
            try:
                sys.stdout.write(
                    str((float(received) / file_length) * 100)[:4] + '%   ' + str(received) + '/' + str(file_length) + ' B\r')
                sys.stdout.flush()
            except:
                pass
            data = s.recv(send_cache)
            if not data:
                break
            received += len(data)
            f.write(data)
    # send heartbeat
    s.sendall("ok")
    sys.stdout.write('100.0%   ' + str(received) + '/' + str(file_length) + ' B\n')
    print("{} receiving successful".format(file_name))
    # return metadata
    return {"status": 200, "msg": "OK"}


def send_file(s, file_path, file_name, send_cache):
    # get size of file to be sent
    file_length = os.path.getsize(file_path)
    # send size of file
    s.sendall("%16d" % file_length)
    # open file and send it
    with open(file_path, 'rb') as f:
        print("{} sending...".format(file_name))
        sent = 0
        while file_length > sent:
            # print progress of upload, ignore if cannot display
            try:
                sys.stdout.write(
                    str((float(sent) / file_length) * 100)[:4] + '%   ' + str(sent) + '/' + str(file_length) + ' B\r')
                sys.stdout.flush()
            except:
                pass
            data = f.read(send_cache)
            s.sendall(data)
            if not data:
                break
            sent += len(data)
    # get heartbeat
    s.recv(2)
    sys.stdout.write('100.0%   ' + str(sent) + '/' + str(file_length) + ' B\n')
    print("{} sending successful".format(file_name))
    # return metadata
    return {"status": 200, "msg": "OK"}


def gen_protlist(__location__):
    # file used for identifying what protocols are available
    # delete contents of file
    with open(__location__ + '/resources/protocols/protlist.txt', "w") as protlist:
        # fill it up with relevvant protocols
        for file in os.listdir(__location__ + '/resources/protocols/'):
            if file.endswith('.py'):
                prot = file[:-3]
                filename = __location__ + '/resources/protocols/' + prot + '.py'
                directory, module_name = os.path.split(filename)
                module_name = os.path.splitext(module_name)[0]

                path = list(sys.path)
                sys.path.insert(0, directory)
                try:
                    module = __import__(module_name)  # cool import command
                except Exception, e:
                    raise e
                else:
                    # write prot into file if successful import
                    protlist.write(prot + '\n')
                finally:
                    sys.path[:] = path


def get_netPass(__location__):
    if not os.path.exists(__location__ + '/resources/networkpass/default.txt'):
        with open(__location__ + '/resources/networkpass/default.txt',
                  "a") as protlist:  # file used for identifying what protocols are available
            pass
        netPass = None
    else:
        with open(__location__ + '/resources/networkpass/default.txt',
                  "r") as protlist:  # file used for identifying what protocols are available
            netpassword = protlist.readline().strip()
        if netpassword != '':
            netPass = netpassword
        else:
            netPass = None
    return netPass


def config(varDic, __location__):
    # if config file does not exist, create one and insert default values.
    # if config files does exist, read values from it
    name = varDic['name']
    if varDic['useConfigPort'] != None:
        usePort = varDic['useConfigPort']
    else:
        usePort = False

    if not os.path.exists(__location__ + '/resources/programparts/' + name + '/config.txt'):
        with open(__location__ + '/resources/programparts/' + name + '/config.txt', "wb") as configs:
            for key, value in varDic.iteritems():
                configs.write('{0}={1}\n'.format(key, value))
    else:
        oldPort = varDic['serverport']
        with open(__location__ + '/resources/programparts/' + name + '/config.txt', "r") as configs:
            for line in configs:
                try:
                    args = line.split('=')
                except:
                    pass
                try:
                    key = args[0].strip()
                    value = args[1].strip()
                    varDic[key] = value
                except Exception, e:
                    print 'Warning in config: %s' % str(e)

        # if doesnt want to use config port, set old one
        if not usePort:
            varDic['serverport'] = oldPort

    return varDic
