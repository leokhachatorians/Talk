import bluetooth as bt
from classes.modals import base_modal
import tkinter as tk
from tkinter import messagebox

class HostServerWindow(base_modal.ModalWindow):
	def body(self, master):
		"""
		Creates and formats everything pertaining to the modal except for
		the buttons.
		"""
		tk.Label(master, text="Port:").grid(row=0)
		tk.Label(master, text="Backlog:").grid(row=1)
		tk.Label(master, text="Timeout:").grid(row=2)

		self.port = tk.Entry(master)
		self.backlog = tk.Entry(master)
		self.time_out = tk.Entry(master)

		self.port.grid(row=0, column=1)
		self.backlog.grid(row=1, column=1) 	
		self.time_out.grid(row=2, column=1)
		return self.port # initial focus

	def button_box(self):
		"""
		Creates the format and style of our buttons
		"""
		box = tk.Frame(self)

		connect_button = tk.Button(box, text="Host", width=10,
			command=self.host_server,
			default=tk.ACTIVE)
		connect_button.pack(side=tk.LEFT, padx=5,pady=5)
		cancel_button = tk.Button(box, text="Cancel", width=10,
			command=self.cancel)
		cancel_button.pack(side=tk.LEFT, padx=5, pady=5)
		self.bind("<Return>", self.host_server)
		box.pack()

	def host_server(self, event=None):
		"""
		Attempts to host a server within the specified timeframe
		the user has selected. If there is a error, which should be due to
		the timeout, we set 'self.error_message' to equal an error message 
		which is then passed into the GUI.

		If succesfully conencted, set 'self.sock' and 'self.server' to their respective
		counter-parts. This will also be passed into the GUI within the calling function.
		"""
		try:
			port = int(self.port.get())
			backlog = int(self.backlog.get())
			time_out = int(self.time_out.get())
		except ValueError:
			messagebox.showerror("Error","Fields can only contain numbers")
		else:
			server = bt.BluetoothSocket(bt.RFCOMM)
			server.settimeout(time_out)
			try:
				server.bind(("",port))
				server.listen(backlog)
				client_sock, client_info = server.accept()
				self.sock = client_sock
				self.server = server
				self.client_info = client_info
			except bt.btcommon.BluetoothError:
				self.sock = None
				self.server = None
				self.error_message = 'No connection before cutoff time of {0} seconds'.format(self.time_out.get())
			finally:
				self.cancel()