import tkinter as tk
import bluetooth as bt
import threading
import queue
import sys

class BlueToothClient():
	def __init__(self, root, message_queue, end_command, start_message_awaiting):
		self.root = root
		self.message_queue = message_queue
		self.end_command = end_command
		self.start_message_awaiting = start_message_awaiting

		# Menu Bar
		self.menubar = tk.Menu(root)
		self.root.config(menu=self.menubar)

		# Add File Tab
		self.file_menu = tk.Menu(self.menubar, tearoff=0)
		self.file_menu.add_command(label='Exit',command=self.end_command)
		self.menubar.add_cascade(label='File',menu=self.file_menu)

		# Add BlueTooth Tab
		self.bt_menu = tk.Menu(self.menubar, tearoff=0)
		self.bt_menu.add_command(label='Scan',
			command=self.discover_nearby_devices)
		self.bt_menu.add_separator()
		self.bt_menu.add_command(label='Connect To',
			command=self.create_connect_to_window)
		self.bt_menu.add_command(label='Host Server',
			command=self.create_host_server_window)
		self.menubar.add_cascade(label='BlueTooth',menu=self.bt_menu)

		# Key Binds
		self.root.bind('<Return>', self.send_message)
		self.root.bind_class("Entry","<Control-v>", self.paste_over_selection)
		self.root.bind_class("Entry","<Control-a>", self.select_all_text)

		# Sockets
		self.sock = None
		self.server = None

		# Chat Receive Display
		self.chat_display = tk.Text(root, width=50)
		self.chat_display.configure(state='disabled',font='helvetica 14')
		self.chat_display.pack(ipady=3)
		self.chat_display.bind("<1>", lambda event: self.chat_display.focus_set())

		# Chat Send Display
		self.chat_send = tk.Entry(root, width=50)
		self.chat_send.pack(ipady=3)
		self.chat_send.focus_set()

		# Send Button
		self.send_button = tk.Button(root, text="Enter", width=50, command=self.send_message, state="disabled")
		self.send_button.pack()

		self.make_right_click_menu(self.root)

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

	def right_click_menu_functionality(self, event, menu):
		menu.post(event.x_root,
			event.y_root)

	def select_all_text(self, event):
		event.widget.selection_range("0","end")

	def paste_over_selection(self, event):
		text_to_paste = self.root.clipboard_get()
		try:
			start = event.widget.focus_get().index('sel.first')
			end = event.widget.focus_get().index('sel.last')
			event.widget.focus_get().delete(start, end)
			event.widget.insert(start, text_to_paste)
		except tk.TclError:
			event.widget.insert(tk.INSERT, text_to_paste)

	def right_click_paste(self):
		text_to_paste = self.root.clipboard_get()
		try:
			start = self.root.focus_get().index('sel.first')
			end = self.root.focus_get().index('sel.last')
			self.root.focus_get().delete(start, end)
			self.root.focus_get().insert(tk.INSERT, text_to_paste)
		except tk.TclError as e:
			self.root.focus_get().insert(tk.INSERT, text_to_paste)

	def make_right_click_menu(self, window):
		# Right click popup menu
		right_click_menu = tk.Menu(window, tearoff=0)
		right_click_menu.add_command(label='Copy',
			accelerator='Ctrl+C',
			command=lambda: window.focus_get().event_generate('<<Copy>>'))
		right_click_menu.add_command(label='Cut',
			command=lambda: window.focus_get().event_generate('<<Cut>>'))
		right_click_menu.add_command(label='Paste',
			accelerator='Ctrl+V',
			command=self.right_click_paste)
		right_click_menu.add_command(label='Delete',
			command=lambda: window.focus_get().event_generate('<<Clear>>'))

		# Bind it
		window.bind('<Button 3>',
			lambda event, menu=right_click_menu: self.right_click_menu_functionality(event,menu))		

	def check_if_not_empty_message(self):
		if not self.chat_send.get():
			return False
		return True

	def display_message(self, message, data=None):
		self.enable_chat_display_state()
		if data:
			self.chat_display.insert('end', message.format(data) + '\n')
		else:
			self.chat_display.insert('end', message + '\n')
		self.disable_chat_display_state()

	def discover_nearby_devices(self):
		self.display_message('Searching for nearby devices...')
		self.chat_display.update_idletasks()
		devices = bt.discover_devices()
		if devices:
			self.display_message('Found the following devices: ')
			for device in devices:
				self.display_message('{0}', device)
		else:
			self.display_message('Unable to find any devices')

	def connect_to_server(self, address, port, child_window, connection=bt.RFCOMM):
		child_window.destroy()
		self.display_message('Trying to connect to: {}', address)
		self.display_message('Port: {}', port)

		try:
			sock = bt.BluetoothSocket(connection)
			sock.connect((address,port))
			self.display_message('Connection Succesful')
			self.sock = sock
			self.enable_send_button()
			self.start_message_awaiting()
		except bt.btcommon.BluetoothError:
			self.display_message('Connection Failed')
			self.sock = None

	def send_message(self, event=None):
		if self.sock:
			try:
				if self.check_if_not_empty_message():
					self.display_message('You: {}', self.chat_send.get())
					self.sock.send(self.chat_send.get())
			except bt.btcommon.BluetoothError as e:
				self.display_message('The connection was lost ')
				self.disable_send_button()
			finally:
				self.clear_chat_send_text()

	def check_message_queue(self):
		while self.message_queue.qsize():
			try:
				data = self.message_queue.get(0).decode('utf-8')
				self.display_message('Them: {}',data)
			except message_queue.Empty:
				pass

	def host_server(self, port, backlog, child_window, connection=bt.RFCOMM):
		child_window.destroy()
		self.display_message('Waiting for connection on port: {}', port)
		self.chat_display.update_idletasks()

		server = bt.BluetoothSocket(connection)
		server.bind(("", port))
		server.listen(backlog)

		client_sock, client_info = server.accept()

		self.display_message('Connected with: {}', client_info)
		self.sock = client_sock
		self.server = server
		self.enable_send_button()
		self.start_message_awaiting()

	def create_host_server_window(self):
		host_server_window = tk.Toplevel()
		host_server_window.title('Create Host Server')
		host_server_window.lift(aboveThis=self.root)

		self.make_right_click_menu(host_server_window)

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

		self.make_right_click_menu(connect_to_window)

		address = tk.Entry(connect_to_window, width=20)
		address.pack(ipady=3)
		address.insert(0,'Address')
		address.focus_set()

		port = tk.Entry(connect_to_window, width=20)
		port.pack(ipady=3)
		port.insert(0,'Port')

		button = tk.Button(connect_to_window, text='Connect', width=20,
			command= lambda: self.connect_to_server(
				address=address.get(),
				port=int(port.get()),
				child_window=connect_to_window))
		button.pack()

class ThreadedClient():
	def __init__(self, master):
		self.master = master
		self.message_queue = queue.Queue()

		self.thread_stop = threading.Event()
		self.running = True

		self.gui = BlueToothClient(master, self.message_queue, self.end_command, self.start_message_awaiting)
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
		self.gui.check_message_queue()
		if not self.running:
			self.stop_threads()
		else:
			self.master.after(100, self.periodic_call)

	def await_messages_thread(self):
		while self.running:
			try:
				self.message_queue.put(self.gui.sock.recv(1024))
			except AttributeError:
				pass

	def end_command(self):
		self.running = False

if __name__ == '__main__':
	master = tk.Tk()
	client = ThreadedClient(master)
	master.mainloop()