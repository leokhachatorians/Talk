from tkinter import *
import bluetooth as bt
import multiprocessing
import threading
from queue import Empty, Full

SERVER = '5C:F3:70:75:AD:2E'
PORT = 1

class BlueToothClient():
	def __init__(self, master, q):
		self.root = master
		self.root.bind('<Return>', self.send_message)
		frame = Frame(master)
		frame.pack()

		self.sock = self.connect_to(SERVER, PORT)

		self.chat_display = Text(master, width=50)
		self.chat_display.configure(state='disabled',font='helvetica 14')
		self.chat_display.pack(ipady=3)

		self.chat_send = Entry(master, width=50)
		self.chat_send.pack(ipady=3)
		self.chat_send.focus_set()

		self.button = Button(master, text="Enter", width=50,command=self.send_message)
		self.button.pack()

		self.root.after(100,self.check_queue,q)

	def display_sent_text(self):
		self.enable_chat_display_state()
		self.chat_display.insert('end',('\nYou: '+self.chat_send.get()))
		self.disable_chat_display_state()
		self.clear_chat_send_text()

	def disable_chat_display_state(self):
		self.chat_display.configure(state='disabled')

	def enable_chat_display_state(self):
		self.chat_display.configure(state='normal')

	def clear_chat_send_text(self):
		self.chat_send.delete(0, 'end')

	def check_if_not_empty_message(self):
		if not self.chat_send.get():
			return False
		return True

	def connect_to(self, address, port,*,connection=bt.RFCOMM):
		sock = bt.BluetoothSocket(connection)
		sock.connect((address,port))
		return sock

	def send_message(self, event=None):
		if self.check_if_not_empty_message():
			self.enable_chat_display_state()
			self.chat_display.insert('end',('\nYou: '+self.chat_send.get()))
			self.disable_chat_display_state()
			self.sock.send(self.chat_send.get())
			self.clear_chat_send_text()

	def check_queue(self, c_queue):
		try:
			data = c_queue.get(0).decode('utf-8')
			#data = data.decode('utf-8')
			self.enable_chat_display_state()
			self.chat_display.insert('end',('\nThem: ' + data))
			self.disable_chat_display_state()
		except Empty:
			pass
		finally:
			self.root.after(100, self.check_queue, c_queue)

def receive_message(q, sock):
	while True:
		q.put(sock.recv(1025))

if __name__ == '__main__':
	root = Tk()
	q = multiprocessing.Queue()
	q.cancel_join_thread()
	app = BlueToothClient(root, q)
	t1 = multiprocessing.Process(target=receive_message,args=(q,app.sock))
	t1.start()
	root.mainloop()