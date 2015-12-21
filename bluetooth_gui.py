import tkinter as tk
import bluetooth as bt
import multiprocessing
import threading
import queue
import time

class BlueToothClient(tk.Frame):
	def __init__(self, root, q):
		self.root = root
		self.q = q

		# Menu Bar
		self.menubar = tk.Menu(root)

		# Add File Tab
		self.file_menu = tk.Menu(self.menubar, tearoff=0)
		self.file_menu.add_command(label='Exit')
		self.menubar.add_cascade(label='File',menu=self.file_menu)

		# Add BlueTooth Tab
		self.bt_menu = tk.Menu(self.menubar, tearoff=0)
		self.bt_menu.add_command(label='Scan')
		self.bt_menu.add_separator()
		self.bt_menu.add_command(label='Connect To',
			command=self.create_connect_to_window)
		self.bt_menu.add_command(label='Host Server',
			command=self.create_host_server_window)
		self.menubar.add_cascade(label='BlueTooth',menu=self.bt_menu)


		self.root.config(menu=self.menubar)

		# Key Binds
		self.root.bind('<Return>', self.send_message)

		frame = tk.Frame(root)
		frame.pack()

		self.sock = None

		# Chat Receive Display
		self.chat_display = tk.Text(root, width=50)
		self.chat_display.configure(state='disabled',font='helvetica 14')
		self.chat_display.pack(ipady=3)

		# Chat Send Display
		self.chat_send = tk.Entry(root, width=50)
		self.chat_send.pack(ipady=3)
		self.chat_send.focus_set()

		# Send Button
		self.button = tk.Button(root, text="Enter", width=50,command=self.send_message)
		self.button.pack()

		self.root.after(100,self.check_queue)

	def delete_child_window(self, window):
		window.destroy()

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

	def connect_to(self, address, port, child_window, *, connection=bt.RFCOMM):
		child_window.destroy()
		sock = bt.BluetoothSocket(connection)
		sock.connect((address,port))
		self.sock = sock

	def send_message(self, event=None):
		if self.check_if_not_empty_message():
			self.enable_chat_display_state()
			self.chat_display.insert('end',('\nYou: '+self.chat_send.get()))
			self.disable_chat_display_state()
			self.sock.send(self.chat_send.get())
			self.clear_chat_send_text()

	def check_queue(self):
		try:
			data = self.q.get(0).decode('utf-8')
			self.enable_chat_display_state()
			self.chat_display.insert('end',('\nThem: ' + data))
			self.disable_chat_display_state()
		except queue.Empty:
			pass
		finally:
			self.root.after(100, self.check_queue)

	def host_server(self, port, backlog, connection=bt.RFCOMM):
		server = bt.BluetoothSocket(connection)
		server.bind(("", port))
		server.listen(backlog)

		self.enable_chat_display_state()
		self.chat_display.insert('end', ('Waiting for connection on port: {0}...'.format(port)))
		self.disable_chat_display_state()

		client_sock, client_info = server.accept()

		self.enable_chat_display_state()
		self.chat_display.insert('end', ('Connected with: {0}'.format(client_info)))
		self.disable_chat_display_state()

		return client_sock

	def create_host_server_window(self):
		scan_window = tk.Toplevel()
		scan_window.title('Create Host Server')
		scan_window.lift(aboveThis=self.root)

		port = tk.Entry(scan_window, width=20)
		port.pack(ipady=3)
		port.insert(0,'Port')
		port.focus_set()

		backlog = tk.Entry(scan_window, width=20)
		backlog.pack(ipady=3)
		backlog.insert(0,'Backlog')

		button = tk.Button(scan_window, text='Create', width=20,
			command= lambda: self.host_server(
				port=int(port.get()),
				backlog=int(backlog.get())))
		button.pack()

	def create_connect_to_window(self):
		connect_to_window = tk.Toplevel()
		connect_to_window.title('Connect')
		connect_to_window.lift(aboveThis=self.root)

		address = tk.Entry(connect_to_window, width=20)
		address.pack(ipady=3)
		address.insert(0,'Address')
		address.focus_set()

		port = tk.Entry(connect_to_window, width=20)
		port.pack(ipady=3)
		port.insert(0,'Port')

		button = tk.Button(connect_to_window, text='Connect', width=20,
			command= lambda: self.connect_to(
				address=address.get(),
				port=int(port.get()),
				child_window=connect_to_window))
		button.pack()


class ThreadedClient():
	def __init__(self, master):
		self.master = master
		self.queue = queue.Queue()

		self.gui = BlueToothClient(master, self.queue)

		self.await_messages = threading.Thread(target=self.await_messages_thread)
		self.await_messages.start()
		self.periodic_call()

	def periodic_call(self):
		self.gui.check_queue()
		self.master.after(100, self.periodic_call)

	def start_await_messages_thread(self):
		self.await_messages.start()

	def await_messages_thread(self):
		while True:
			try:
				self.queue.put(self.gui.sock.recv(1024))
			except AttributeError:
				time.sleep(2)
				pass

def receive_message(q, sock):
	while True:
		q.put(sock.recv(1025))

if __name__ == '__main__':
	root = tk.Tk()
	client = ThreadedClient(root)
	root.mainloop()
