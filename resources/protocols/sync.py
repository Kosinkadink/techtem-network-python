#!/usr/bin/python2
import sys, socket, select, os, threading, sqlite3
from time import strftime, sleep, time, ctime
from hashlib import sha1, md5
from datetime import datetime
from getpass import getpass

common_location = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))  # directory from which this script is ran
main_dir = os.path.realpath(os.path.join(common_location, '..'))
sys.path.insert(0, os.path.join(main_dir, 'source/'))
import CommonCode_Client

# universal variables
variables = []
standalone = True
version = '3.0.0'
standalonefunction = 'standalone_function'
__location__ = None
clientfunction = None
serverfunction = 'server_function'


# script-specific variables

class SyncClient(CommonCode_Client.TemplateProt):
    # don't change this
    threads = []
    doAutoSync = False  # toggled by user
    isSyncing = False  # toggled by program
    syncInterval = 60
    preferredSumType = 'time'
    continueRunning = True
    # change this for client
    varDict = dict(send_cache=409600, scriptname='sync', scriptfunction='sync_client', version='3.0.0')

    def __init__(self, location, startTerminal):
        global __location__
        __location__ = location
        CommonCode_Client.TemplateProt.__init__(self, location, startTerminal)

    def run_processes(self):
        if self.startTerminal:
            # launch auto sync thread
            syncprocess = threading.Thread(target=self.autoSyncThread)
            syncprocess.daemon = True
            self.threads.append(syncprocess)
            syncprocess.start()
            # now do server terminal
            self.serverterminal()

    def set_funcMap(self):
        self.funcMap = {
            'sync': self.syncCommand,
            'time': self.timeCommand,
            'newuser': self.newUserCommand,
            'checkauth': self.checkAuthCommand
        }

    def init_spec(self):

        # sync files start
        if not os.path.exists(__location__ + '/resources/programparts/sync'): os.makedirs(
            __location__ + '/resources/programparts/sync')

        if not os.path.exists(__location__ + '/resources/programparts/sync/serverlist.txt'):
            with open(__location__ + '/resources/programparts/sync/serverlist.txt', "a") as seeds:
                seeds.write("""####################################################
##The format is: ||ip:port||
##Files will be sent to and from these servers
##Only lines starting with || will be read
####################################################""")
                # sync files end

    def boot(self):
        self.clear()
        print "TechTem Sync Client started"
        print "Version " + self.varDict["version"]
        print "Type help for command list\n"

    def help(self):
        print "\nclear: clears screen"
        print "exit: closes program"
        print "time: receive server time"
        print "newacc: create new account on server"
        print "createsync: create a new sync state"
        print "sync: sync client files with server"
        print "login: set username and password for client"
        print "size: check size of user directory client-side"
        print "encrypt OR enc: toggle encryption status"
        print "autosync OR auto: toggle autosync status"
        print "interval OR int + number: set interval in seconds between autosync attempts"

    # function for client splash screen
    def serverterminal(self):
        self.boot()
        while True:
            inp = raw_input(">")
            try:
                if inp:
                    if inp.split()[0] == 'quit' or inp.split()[0] == 'leave' or inp.split()[0] == 'exit':
                        break
                    elif inp.split()[0] == 'clear':
                        self.boot()
                    elif inp.split()[0] in ['autosync', 'auto']:
                        self.toggleAutoSync()
                    elif inp.split()[0] in ['interval', 'int']:
                        self.setSyncInterval(inp)
                    elif inp.split()[0] == 'time':
                        print self.connectTime()
                    elif inp.split()[0] == 'help' or inp.split()[0] == '?':
                        self.help()
                    elif inp.split()[0] == 'login':
                        self.loginAsOther()
                    elif inp.split()[0] == 'newacc':
                        self.connectCreateNew()
                    elif inp.split()[0] == 'check':
                        self.loginAsOther()
                    elif inp.split()[0] == 'createsync':
                        self.createSyncState()
                    elif inp.split()[0] == 'sync':
                        self.connectSync()
                    elif inp.split()[0] == 'size':
                        self.checkSize()
                    elif inp.split()[0] == 'sum':
                        self.checkChecksum(inp.split()[1])
                    elif inp.split()[0] == 'netpass':
                        self.get_netPass()
                        print self.netPass
                    else:
                        print "Invalid command"
            except Exception, e:
                print str(e)

    def setSyncInterval(self, inp):
        try:
            prelimVal = int(inp.split()[1])
        except Exception, e:
            print "Improper sync interval; %s" % str(e)
        else:
            if prelimVal > 1:
                self.syncInterval = prelimVal
                print "Sync interval changed to %s seconds" % self.syncInterval

    def toggleAutoSync(self):
        if self.doAutoSync:
            self.doAutoSync = False
            print "Auto Sync is now OFF"
        else:
            self.doAutoSync = True
            print "Auto Sync is now ON"

    def checkSize(self):
        self.login()
        try:
            start = time()
            print self.sizeDir(__location__ + '/resources/programparts/sync/%s' % self.username.lower())
            end = time()
            print str(end - start)
        except Exception, e:
            print str(e)

    def userSize(self, username):
        self.login()
        return str(self.sizeDir(__location__ + '/resources/programparts/sync/%s' % self.username.lower()))

    def checkChecksum(self, type):
        self.login()
        try:
            start = time()
            list = self.checksumList(__location__ + '/resources/programparts/sync/%s' % self.username.lower(), type)
            end = time()
            print list
            print str(end - start)
        except Exception, e:
            print str(e)

    def createSyncState(self):
        try:
            valid = self.connectCheckAuth()
            if not valid:
                raise ValueError("authentication error")
            username = self.username
            if not os.path.exists(__location__ + '/resources/programparts/sync/%s' % username):
                os.makedirs(__location__ + '/resources/programparts/sync/%s' % username)
                with open(__location__ + '/resources/programparts/sync/%s/timestamp.txt' % username, "a") as timedoc:
                    timedoc.write("""00000000000000""")
            else:
                if not os.path.exists(__location__ + '/resources/programparts/sync/%s/timestamp.txt' % username):
                    with open(__location__ + '/resources/programparts/sync/%s/timestamp.txt' % username,
                              "a") as timedoc:
                        timedoc.write("""00000000000000""")
                else:
                    os.remove(__location__ + '/resources/programparts/sync/%s/timestamp.txt' % username)
                    timestamp = self.connectTime()
                    with open(__location__ + '/resources/programparts/sync/%s/timestamp.txt' % username,
                              "a") as timedoc:
                        timedoc.write(timestamp)
            print 'Creating sync state...'
            with open(__location__ + '/resources/programparts/sync/%s/timestamp.txt' % username, "a") as timedoc:
                list = self.checksumList(__location__ + '/resources/programparts/sync/%s' % username.lower(),
                                         self.preferredSumType)
                for item in list:
                    timedoc.write('\n' + item)
            print 'Sync state created.'
        except Exception, e:
            print str(e) + '\n'

    def connectSync(self):
        if (self.isSyncing):
            print 'Program is already syncing'
            return
        else:
            self.isSyncing = True
        try:
            self.createSyncState()
            # valid = self.connectCheckAuth()
            # if not valid:
            #	return
            username = self.username
            if not os.path.exists(__location__ + '/resources/programparts/sync/%s' % username):
                os.makedirs(__location__ + '/resources/programparts/sync/%s' % username)
                with open(__location__ + '/resources/programparts/sync/%s/timestamp.txt' % username, "a") as timedoc:
                    timedoc.write("""00000000000000""")
            else:
                if not os.path.exists(__location__ + '/resources/programparts/sync/%s/timestamp.txt' % username):
                    with open(__location__ + '/resources/programparts/sync/%s/timestamp.txt' % username,
                              "a") as timedoc:
                        timedoc.write("""00000000000000""")
            dirSize = self.userSize(username)
            print self.connectToServer('spec' + dirSize, 'sync')

        except Exception, e:
            print str(e) + '\n'
        finally:
            self.isSyncing = False

    def login(self):
        if (self.username == None or self.password == None):
            return self.loginAsOther()
        else:
            try:
                # make sure lengths are okay
                if len(self.username) < 19 and len(self.password) < 129:
                    print "Username and Password entered"
                    return True
                else:
                    print "Improper number of characters, try again."
                    raise ValueError("incorrect # of characters")
            except Exception, e:
                print str(e)
                self.username = None
                self.password = None
                return False

    def loginAsOther(self):
        username = self.username
        password = self.password
        try:
            self.username = raw_input("Username: ").lower()
            self.password = getpass("Password: ")
            # make sure lengths are okay
            if len(self.username) < 19 and len(self.password) < 129:
                print "Username and Password entered"
                valid = self.connectCheckAuth()
                if not valid:
                    raise (ValueError("authentication error"))
                else:
                    return True
            else:
                print "Improper number of characters, try again."
                raise ValueError("incorrect # of characters")
        except Exception, e:
            print str(e)
            self.username = None
            self.password = None
            return False

    def loginnew(self):
        username = self.username
        password = self.password
        try:
            self.username = raw_input("Username: ").lower()
            self.password = getpass("Password: ")
            password2 = getpass("Re-enter Password: ")
            # make sure passwords match and lengths are okay
            if self.password == password2 and len(self.username) < 19 and len(self.password) < 129:
                print "Username and Password entered"
                return True
            else:
                print "Passwords do not match, try again."
                raise ValueError("password mismatch")
        except Exception, e:
            print str(e)
            self.username = None
            self.password = None
            return False

    def sizeDir(self, folder):  # get size of directory and all subdirectories
        if os.name == 'nt':
            folder = folder.replace('\\', '/')
        total_size = os.path.getsize(folder)
        for item in os.listdir(folder):
            itempath = os.path.join(folder, item)
            if os.path.isfile(itempath):
                total_size += os.path.getsize(itempath)
            # checksum(itempath)
            elif os.path.isdir(itempath):
                total_size += self.sizeDir(itempath)
        return total_size

    def checksumList(self, itempath, type):
        username = self.username
        folder = itempath
        checksumlist = []
        if type == 'md':
            for item in os.listdir(folder):
                itempath = os.path.join(folder, item)
                if os.name == 'nt':
                    itempath = itempath.replace('\\', '/')
                if os.path.isfile(itempath):
                    gene = itempath.split(__location__ + '/resources/programparts/sync/%s/' % username)[1:]
                    listLength = len(gene)
                    if listLength > 1:
                        actual = ''
                        number = 0
                        while number < listLength:
                            actual += gene[number]
                            if (number + 1) != listLength:
                                actual += '/resources/programparts/sync/%s/' % username
                    else:
                        actual = gene[0]
                    checksumlist += [actual + self.checksum(itempath)]
                # print "%s: %s" % (actual,ctime(os.path.getmtime(itempath)))
                # checksum(itempath)
                elif os.path.isdir(itempath):
                    checksumlist += self.checksumList(itempath, type)
            return checksumlist
        elif type == 'sh':
            for item in os.listdir(folder):
                itempath = os.path.join(folder, item)
                if os.name == 'nt':
                    itempath = itempath.replace('\\', '/')
                if os.path.isfile(itempath):
                    gene = itempath.split(__location__ + '/resources/programparts/sync/%s/' % username)[1:]
                    listLength = len(gene)
                    if listLength > 1:
                        actual = ''
                        number = 0
                        while number < listLength:
                            actual += gene[number]
                            if (number + 1) != listLength:
                                actual += __location__ + '/resources/programparts/sync/%s/' % username
                    else:
                        actual = gene[0]
                    checksumlist += [actual + self.checksum2(itempath)]
                # checksum(itempath)
                elif os.path.isdir(itempath):
                    checksumlist += self.checksumList(itempath, type)
            return checksumlist
        elif type == 'time':
            for item in os.listdir(folder):
                itempath = os.path.join(folder, item)
                if os.name == 'nt':
                    itempath = itempath.replace('\\', '/')
                if os.path.isfile(itempath):
                    gene = itempath.split(__location__ + '/resources/programparts/sync/%s/' % username)[1:]
                    listLength = len(gene)
                    if listLength > 1:
                        actual = ''
                        number = 0
                        while number < listLength:
                            actual += gene[number]
                            if (number + 1) != listLength:
                                actual += __location__ + '/resources/programparts/sync/%s/' % username
                    else:
                        actual = gene[0]
                    checksumlist += [actual + self.checkmoddate(itempath)]
                # checksum(itempath)
                elif os.path.isdir(itempath):
                    checksumlist += self.checksumList(itempath, type)
            return checksumlist

    def checkmoddate(self, itempath):
        modstring = ctime(os.path.getmtime(itempath))
        moddate = datetime.strptime(modstring, "%a %b %d %H:%M:%S %Y")
        UTC_TIMEDELTA = datetime.utcnow() - datetime.now()
        utcdate = moddate + UTC_TIMEDELTA
        return '::' + utcdate.strftime("%Y%m%d%H%M%S")

    def checksum(self, itempath):
        if os.path.getsize(itempath) < 50240000:
            data = md5(open(itempath).read()).hexdigest()
            # print '[%s]' % data
            return '::' + data
        else:
            # print '['
            with open(itempath) as file:
                datamult = '::'
                while True:
                    data = file.read(50240000)
                    if data:
                        data = md5(data).hexdigest()
                        datamult += data
                    # print data
                    else:
                        break
                # print ']'
                # print 'Checksum complete.'
                return datamult

    def sizeDir2(self, folder):  # get size of directory and all subdirectories
        total_size = os.path.getsize(folder)
        for item in os.listdir(folder):
            itempath = os.path.join(folder, item)
            if os.path.isfile(itempath):
                total_size += os.path.getsize(itempath)
                self.checksum2(itempath)
            elif os.path.isdir(itempath):
                total_size += self.sizeDir2(itempath)
        return total_size

    def checksum2(self, itempath):
        if os.path.getsize(itempath) < 50240000:
            data = sha1(open(itempath).read()).hexdigest()
            # print '[%s]' % data
            return '::' + data

        else:
            # print '['
            with open(itempath) as file:
                datamult = '::'
                while True:
                    data = file.read(50240000)
                    if data:
                        data = sha1(data).hexdigest()
                        datamult += data
                    # print data
                    else:
                        break
                # print ']'
                # print 'Checksum complete.'
                return datamult

    def requestUserToken(self):
        try:
            token = raw_input("Token: ")
            if len(token) < 128:
                return True, token
            else:
                return False, None
        except Exception, e:
            print str(e)
            return False, None

    def connectCheckAuth(self):
        # global username, password
        try:
            valid = self.login()
            if valid:
                pass
            if not valid:
                raise ValueError("login entry error")
            return self.connectToServer('checkAuth', 'checkauth')

        except Exception, e:
            print str(e) + '\n'

    def connectCreateNew(self):
        # global username, password
        try:
            valid = self.loginnew()
            if valid:
                pass
            if not valid:
                raise ValueError("login entry error")
            valid, token = self.requestUserToken()
            if not valid:
                raise ValueError("token entry error")

            self.connectToServer(token, 'newuser')

        except Exception, e:
            print str(e) + '\n'

    def connectTime(self):
        time = self.connectToServer('savedtime', 'time')
        # print time
        return time

    def connectToServer(self, data, command):
        with open(__location__ + '/resources/programparts/sync/serverlist.txt', "r") as seeds:
            for line in seeds:
                if line.startswith('||'):
                    # try: #connect to ip, save data, issue command
                    return self.connectip(self, line.split("||")[1], data, command)
        print ''

    def sendItem(self, s):  # send file to seed

        start = time()
        username = self.username
        gene = s.recv(1024)
        print 'sending data'
        print 'awaiting reply'

        file_name = gene.split('/')[-1]

        file = __location__ + '/resources/programparts/sync/%s/' % username + gene

        # print os.path.join(uploads, file_name)
        print file
        if os.path.exists(file):
            print file_name + " found"
            s.sendall('ok')

            use_cache = s.recv(16)
            use_cache = int(use_cache.strip())

            filelength = os.path.getsize(file)
            s.sendall('%16d' % filelength)

            s.recv(2)
            with open(file, 'rb') as f:
                print file_name + " sending..."
                sent = 0
                while True:
                    try:
                        sys.stdout.write(str((float(sent) / filelength) * 100)[:4] + '%   ' + str(sent) + '/' + str(
                            filelength) + ' B\r')
                        sys.stdout.flush()
                    except:
                        pass
                    data = f.read(use_cache)
                    if not data:
                        break
                    sent += len(data)
                    s.sendall(data)
            s.recv(2)
            sys.stdout.write('100.0%   ' + str(sent) + '/' + str(filelength) + ' B\n')
            print file_name + " sending successful"

        else:
            print file_name + " not found"
            s.sendall('no')

    def sendTimestamp(self, s):  # send file to seed
        username = self.username
        data = __location__ + '/resources/programparts/sync/%s/timestamp.txt' % username
        if os.name == 'nt':
            data = data.replace('\\', '/')
        print 'sending data'
        dataloc = __location__
        if os.name == 'nt':
            dataloc = dataloc.replace('\\', '/')
        s.sendall(dataloc + '/resources/programparts/sync/%s/timestampclient.txt' % username)
        print 'awaiting reply'
        s.recv(2)

        file = data

        uploads = __location__ + '/resources/uploads/'

        file_name = data.split('/')[-1]

        print file
        if os.path.exists(file):
            print file_name + " found"
            s.sendall('ok')
            s.recv(2)

            filelength = os.path.getsize(file)
            s.sendall('%16d' % filelength)
            with open(file, 'rb') as f:
                print file_name + " sending..."
                sent = 0
                while True:
                    sys.stdout.write(str((float(sent) / filelength) * 100)[:4] + '%' + '\r')
                    sys.stdout.flush()
                    data = f.read(10240)
                    if not data:
                        break
                    sent += len(data)
                    s.sendall(data)

            s.recv(2)
            sys.stdout.write('100.0%\n')
            print file_name + " sending successful"

        else:
            print file_name + " not found"

    def sendFileList(self, s, files):  # send file list
        data = files
        s.sendall('%16d' % len(data))
        print "file list sending..."
        s.sendall(data)
        s.recv(2)
        print "file list sending successful"

    def sendCommand(self, s, data):  # send sync files to server
        username = self.username
        folder = __location__ + '/resources/programparts/sync/%s/' % username

        if data == 'sync':
            filessent = self.sendSyncFiles(s, folder)
            print filessent
            s.sendall('n')
            s.recv(2)
            files = '@%$%@'
            for fileloc in filessent:
                files += fileloc + '@%$%@'
            self.sendFileList(s, files)
        elif data == 'spec':
            self.sendSpecFiles(s)
        else:
            s.sendall('n')
            return 'unknown response'

    def sendSyncFiles(self, s, folder):

        # total_size = os.path.getsize(folder)
        syncedfiles = []
        for item in os.listdir(folder):
            itempath = os.path.join(folder, item)
            if os.name == 'nt':
                itempath = itempath.replace('\\', '/')
            if os.path.isfile(itempath):
                syncedfiles += [itempath]
                s.sendall('y')
                s.recv(2)
                self.sendItem(s, itempath)
            elif os.path.isdir(itempath):
                syncedfiles += self.sendSyncFiles(s, itempath)
        return syncedfiles

    def sendSpecFiles(self, s):
        username = self.username
        s.sendall('ok')
        s.recv(2)
        while True:
            s.sendall('ok')
            sending = s.recv(1)
            if sending == 'y':
                s.sendall('ok')
                print 'receiving location...'
                self.sendItem(s)
            else:
                break
        pass

    def recvSpecFiles(self, s):
        username = self.username
        s.sendall('ok')
        s.recv(2)
        while True:
            s.sendall('ok')
            sending = s.recv(1)
            if sending == 'y':
                s.sendall('ok')
                self.sync_recv_file(s, username)
            else:
                break
        pass

    def receiveSyncCommand(self, s, data):
        username = self.username
        self.recvSpecFiles(s)
        files = []
        with open(__location__ + '/resources/programparts/sync/%s/timestamp.txt' % username, 'rb') as timedoc:
            for line in timedoc:
                files += [line]
        files = files[1:]
        # print files
        folder = __location__ + '/resources/programparts/sync/%s/' % username
        if os.name == 'nt':
            folder = folder.replace('\\', '/')

        filelist = []
        for file in files:
            # print file
            file = file.split('::')[0]
            file = folder + file
            filelist += [file]

        self.removeUnsyncedFiles(s, folder, filelist)

    def receiveCommand(self, s, data):  # loops receiving files until master denies
        username = self.username
        while True:
            sending = s.recv(1)
            s.sendall('ok')
            if sending == 'y':
                self.sync_recv_file(s, username)
            else:
                break
        s.sendall('ok')
        files = self.recv_file_list(s)
        files = files.split('@%$%@')[1:-1]
        folder = __location__ + '/resources/programparts/sync/%s/' % username
        print folder
        if os.name == 'nt':
            folder = folder.replace('\\', '/')
        localfiles = []
        print folder
        for file in files:
            splitfile = file.split('/resources/programparts/sync/%s/' % username)[1]
            localfiles += [folder + splitfile]
        print localfiles
        print 'location: %s' % __location__
        print 'folder: %s' % folder
        self.removeUnsyncedFiles(s, folder, localfiles)

    def removeUnsyncedFiles(self, s, folder, files):
        # total_size = os.path.getsize(folder)
        syncedfiles = []
        for item in os.listdir(folder):
            itempath = os.path.join(folder, item)
            if os.name == 'nt':
                itempath = itempath.replace('\\', '/')
            if os.path.isfile(itempath):
                syncedfiles += [itempath]
                if not itempath in files:
                    print 'removing %s' % itempath
                    os.remove(itempath)
            elif os.path.isdir(itempath):
                syncedfiles += self.removeUnsyncedFiles(s, itempath, files)

        self.removeUnsyncedFolders(folder)

        return syncedfiles

    def removeUnsyncedFolders(self, folder):
        files = os.listdir(folder)
        # remove empty subfolders
        if len(files):
            for f in files:
                # if os.name == 'nt':
                #	f = f.replace('\\','/')
                fullpath = os.path.join(folder, f)
                if os.path.isdir(fullpath):
                    self.removeUnsyncedFolders(fullpath)
        # if folder empty, delete it
        files = os.listdir(folder)
        if len(files) == 0:
            os.rmdir(folder)

    def sync_recv_file(self, s, username):  # receives files from client
        gene = s.recv(1024)
        s.send('ok')
        print gene
        filelocpre = gene.split('/resources/programparts/sync/%s/' % username, 1)[1]
        filename = filelocpre.split('/')[-1]
        filelocpre = filelocpre.split('/')[:-1]
        fileloc = ''
        for file in filelocpre:
            fileloc += file + '/'

        downloadslocation = __location__ + '/resources/programparts/sync/%s/' % username + fileloc

        has = s.recv(2)
        if has != 'ok':
            return '404'
        else:
            use_cache = s.recv(16)
            use_cache = int(use_cache.strip())

            s.sendall('ok')
            size = s.recv(16)
            size = int(size.strip())
            s.sendall('ok')
            recvd = 0
            print filename + ' download in progress...'
            if not os.path.exists(downloadslocation):
                os.makedirs(downloadslocation)
            q = open(os.path.join(downloadslocation, filename), 'wb')
            while size > recvd:
                sys.stdout.write(str((float(recvd) / size) * 100)[:4] + '%' + '\r')
                sys.stdout.flush()
                data = s.recv(use_cache)
                if not data:
                    break
                recvd += len(data)
                q.write(data)
            s.sendall('ok')
            q.close()
            sys.stdout.write('100.0%\n')
            print filename + ' download complete'
            return '111'

    def recv_file_list(self, s):  # receives files from client

        size = s.recv(16)
        size = int(size.strip())
        recvd = 0
        print  'file names download in progress...'
        list = ''
        while size > recvd:
            sys.stdout.write(str((float(recvd) / size) * 100)[:4] + '%' + '\r')
            sys.stdout.flush()
            data = s.recv(1024)
            if not data:
                break
            recvd += len(data)
            list += data
        s.sendall('ok')
        sys.stdout.write('100.0%\n')
        print 'file names download complete'
        return list

    def isValidSize(self, s, size_dir):
        s.sendall(size_dir)
        valid = s.recv(1)
        if valid == 'y':
            return True
        else:
            return False

    def isAvailable(self, s):
        s.sendall('k')
        available = s.recv(1)
        if available == 'y':
            return True
        else:
            return False

    def syncCommand(self, s, data):
        size_dir = data[4:]
        data = data[:4]
        valid = self.checkAuthCommand(s, data)
        if not valid:
            return "authentication error"
        # with open(__location__+'/resources/programparts/sync/%s/timestamp.txt' % username, "rb") as timedoc:
        #	timestamp = timedoc.readline()

        available = self.isAvailable(s)
        if not available:
            s.sendall('ok')
            response = s.recv(1024)
            return response
        s.sendall('ok')

        # now send timestamp
        self.sendTimestamp(s)

        print size_dir
        valid = self.isValidSize(s, size_dir)
        if not valid:
            s.send('ok')
            response = s.recv(1024)
            return response
        s.send('ok')

        works = s.recv(2)
        if works != 'ok':
            s.sendall('ok')
            response = s.recv(128)
            return response
        s.sendall('ok')
        action = s.recv(4)
        if action == 'send':
            self.sendCommand(s, data)
            return 'Sync complete.'
        elif action == 'recv':
            self.receiveSyncCommand(s, data)
            return 'Sync complete.'
        elif action == 'same':
            return 'already synced'

    def checkAuthCommand(self, s, data):
        username = self.username
        password = self.password
        s.sendall(username)
        valid = s.recv(1)
        if valid == 'n':
            print 'Username is invalid'
            return False
        s.sendall(password)
        match = s.recv(1)
        if match == 'y':
            print 'Correct Username/Password Combo'
            return True
        else:
            print 'Incorrect Username/Password Combo'
            return False

    def newUserCommand(self, s, data):
        username = self.username
        password = self.password
        s.sendall(username)
        proper = s.recv(1)
        if proper == 'y':
            s.sendall(password)
            response = s.recv(1)
            if response == 'y':
                s.sendall('ok')
                need_token = s.recv(2)
                print 'need token: %s' % need_token
                if need_token == 'rt':
                    print 'trying to send token...'
                    s.sendall(data)
                    print 'done sending token'
                    validToken = s.recv(1)
                    if validToken != 'y':
                        s.sendall('ok')
                        print s.recv(128)
                        return

                print 'Account created.'
                if not os.path.exists(__location__ + '/resources/programparts/sync/%s' % username):
                    os.makedirs(__location__ + '/resources/programparts/sync/%s' % username)
                    with open(__location__ + '/resources/programparts/sync/%s/timestamp.txt' % username,
                              "a") as timedoc:
                        timedoc.write("""00000000000000""")
                else:
                    if not os.path.exists(__location__ + '/resources/programparts/sync/%s/timestamp.txt' % username):
                        with open(__location__ + '/resources/programparts/sync/%s/timestamp.txt' % username,
                                  "a") as timedoc:
                            timedoc.write("""00000000000000""")
            else:
                s.send('ok')
                print s.recv(128)
        else:
            s.send('ok')
            print s.recv(128)

    def timeCommand(self, s, data):
        s.sendall('send')
        time = s.recv(128)
        return time

    def exit(self):
        quit()

    def autoSyncThread(self):
        while (self.continueRunning):
            if (self.doAutoSync and self.isSyncing != True and self.username != None and self.password != None):
                try:
                    self.connectSync()
                except:
                    pass
                sleep(self.syncInterval)
            else:
                sleep(10)


def standalone_function(data, location, startTerminal):
    SyncClient(location, startTerminal)
    return "Left sync client, back in main client"


def server_function(location):
    return SyncClient(location, False)
