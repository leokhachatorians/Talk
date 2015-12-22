import bluetooth as bt
import multiprocessing

def receive_messages(sock):
	try:
		while True:
			print('Received Messages: {0}'.format(sock.recv(1024)))
	except bt.btcommon.BluetoothError as e:
		raise

port = 1
backlog = 1

serv = bt.BluetoothSocket(bt.RFCOMM)
serv.bind(("", port))
serv.listen(backlog)

client_s, client_i = serv.accept()
print('Succesfully connected with: ', client_i)

try:
	check_messages = multiprocessing.Process(target=receive_messages,
		args=(client_s,))
	check_messages.start()

	while True:
		message = input('Message: ')
		client_s.send(message)
except Exception as e:
	print('Error: {0}'.format(e))