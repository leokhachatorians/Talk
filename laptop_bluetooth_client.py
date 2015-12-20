import bluetooth as bt
import asyncio
import multiprocessing

SERVER = '5C:F3:70:75:AD:2E'
PORT = 1

def discover_devices():
	devices = bt.discover_devices()
	return devices

def get_service(address):
	service = bt.find_service(address=address)
	return service

def connect_to(address, port,*,connection=bt.RFCOMM):
	sock = bt.BluetoothSocket(connection)
	sock.connect((address,port))
	return sock

def close_connection(sock):
	sock.close()

def send_message(sock):
	message = input('Message: ')
	sock.send(message)

def receive_message(sock):
	while True:
		print('Received Message: {0}'.format(sock.recv(1024)))

sock = connect_to(SERVER,PORT)
try:
	get = multiprocessing.Process(target=receive_message, args=(sock,))
	get.start()
	while True:
		send_message(sock)
except Exception as e:
	print('Closing down: {0}'.format(e))
	get.terminate()
finally:
	sock.close()
	exit()