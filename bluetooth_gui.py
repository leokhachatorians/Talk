import tkinter as tk
import bluetooth as bt
import multiprocessing
import threading
import queue
import time
import sys
import select

class BlueToothClient():
	def __init__(self, root, queue, end_command, start_message_awaiting):
		self.root = root
		self.queue = queue
		self.end_command = end_command
		self.start_message_awaiting = start_message_awaiting

		# Menu Bar
		self.menubar = tk.Menu(root)

		# Add File Tab
		self.file_menu = tk.Menu(self.menubar, tearoff=0)
		self.file_menu.add_command(label='Exit',command=self.end_command)
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

		self.sock = None
		self.server = None

		# Chat Receive Display
		self.chat_display = tk.Text(root, width=50)
		self.chat_display.configure(state='disabled',font='helvetica 14')
		self.chat_display.pack(ipady=3)

		# Chat Send Display
		self.chat_send = tk.Entry(root, width=50)
		self.chat_send.pack(ipady=3)
		self.chat_send.focus_set()

		# Send Button
		self.send_button = tk.Button(root, text="Enter", width=50, command=self.send_message, state="disabled")
		self.send_button.pack()

	def delete_child_window(self, window):
		window.destroy()

	def disable_chat_display_state(self):
		self.chat_display.configure(state='disabled')

	def enable_chat_display_state(self):
		self.chat_display.configure(state='normal')

	def enable_send_button(self):
		self.send_button.config(state="normal")

	def disable_send_button(self):
		self.send_button.config(state="disabled")

	def clear_chat_send_text(self):
		self.chat_send.delete(0, 'end')

	def check_if_not_empty_message(self):
		if not self.chat_send.get():
			return False
		return True

	def display_message(self, message, data=None):
		self.enable_chat_display_state()
		if data:
			self.chat_display.insert('end', message.format(data))
		else:
			self.chat_display.insert('end', message)
		self.disable_chat_display_state()

	def connect_to(self, address, port, child_window, connection=bt.RFCOMM):
		child_window.destroy()
		self.display_message('Trying to connect to: {} \n', address)
		self.display_message('Port: {} \n', port)

		try:
			sock = bt.BluetoothSocket(connection)
			sock.connect((address,port))
			self.display_message('Connection Succesful \n')
			self.sock = sock
			self.enable_send_button()
			self.start_message_awaiting()
		except bt.btcommon.BluetoothError:
			self.display_message('Connection Failed \n')
			self.sock = None

	def send_message(self, event=None):
		if self.sock:
			try:
				if self.check_if_not_empty_message():
					self.display_message('You: {} \n', self.chat_send.get())
					self.sock.send(self.chat_send.get())
			except bt.btcommon.BluetoothError as e:
				self.display_message('The connection was lost \n')
				self.disable_send_button()
			finally:
				self.clear_chat_send_text()

	def check_queue(self):
		while self.queue.qsize():
			try:
				data = self.queue.get(0).decode('utf-8')
				self.display_message('Them: {} \n',data)
			except queue.Empty:
				pass

	def host_server(self, port, backlog, child_window, connection=bt.RFCOMM):
		self.display_message('Waiting for connection on port: {}\n', port)
		child_window.destroy()

		server = bt.BluetoothSocket(connection)
		server.bind(("", port))
		server.listen(backlog)

		client_sock, client_info = server.accept()

		self.display_message('Connected with: {}\n', client_info)
		self.sock = client_sock
		self.server = server
		self.enable_send_button()
		self.start_message_awaiting()

	def create_host_server_window(self):
		host_server_window = tk.Toplevel()
		host_server_window.title('Create Host Server')
		host_server_window.lift(aboveThis=self.root)

		port = tk.Entry(host_server_window, width=20)
		port.pack(ipady=3)
		port.insert(0,'Port')
		port.focus_set()

		backlog = tk.Entry(host_server_window, width=20)
		backlog.pack(ipady=3)
		backlog.insert(0,'Backlog')

		button = tk.Button(host_server_window, text='Create', width=20,
			command= lambda: self.host_server(
				port=int(port.get()),
				backlog=int(backlog.get()),
				child_window=host_server_window))
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

		self.thread_stop = threading.Event()
		self.running = True

		self.gui = BlueToothClient(master, self.queue, self.end_command, self.start_message_awaiting)
		self.periodic_call()

	def start_message_awaiting(self):
		self.thread_stop.clear()
		self.await_messages = threading.Thread(target=self.await_messages_thread,
			daemon=True)
		self.await_messages.start()

	def stop_threads(self):
		try:
			sys.exit(1)
		except Exception as e:
			print(e)

	def periodic_call(self):
		self.gui.check_queue()
		if not self.running:
			self.stop_threads()
		else:
			self.master.after(100, self.periodic_call)

	def await_messages_thread(self):
		while self.running:
			try:
				self.queue.put(self.gui.sock.recv(1024))
			except AttributeError:
				pass

	def end_command(self):
		self.running = False

if __name__ == '__main__':
	master = tk.Tk()
	client = ThreadedClient(master)
	master.mainloop()