import socket

variables = ['url']
standalone = False
version = '3.0.0'
clientfunction = 'name_function'
serverfunction = None

def name_function(cliObj):

	s = cliObj.s
	data = cliObj.data

	s.sendall('name')
	s.recv(2)
	url = data[0]

	rqst = str(url)
	print 'requesting ip'
	s.sendall(rqst)
	has = s.recv(1)
	s.sendall('ok')
	#get message
	ip = s.recv(1024)
	return ip