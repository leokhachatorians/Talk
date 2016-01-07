import bluetooth as bt
from classes.modals import base_modal
import tkinter as tk
from tkinter import messagebox

class ConnectToServerWindow(base_modal.ModalWindow):
	def body(self, master):

		tk.Label(master, text="Adress:").grid(row=0)
		tk.Label(master, text="Port:").grid(row=1)

		self.address = tk.Entry(master)
		self.port = tk.Entry(master)

		self.address.grid(row=0, column=1)
		self.port.grid(row=1, column=1)
		return self.address # initial focus

	def button_box(self):
		box = tk.Frame(self)

		connect_button = tk.Button(box, text="Connect", width=10,
			command=self.connect,
			default=tk.ACTIVE)
		connect_button.pack(side=tk.LEFT, padx=5,pady=5)
		cancel_button = tk.Button(box, text="Cancel", width=10,
			command=self.cancel)
		cancel_button.pack(side=tk.LEFT, padx=5, pady=5)
		self.bind("<Return>", self.connect)
		box.pack()

	def connect(self, event=None):
		try:
			port = int(self.port.get())
			address = self.address.get()
		except ValueError:
			messagebox.showerror("Error","Port must be an integer")
		else:
			try:
				sock = bt.BluetoothSocket(bt.RFCOMM)
				sock.connect((address, port))
				self.sock = sock
				self.address = address
				self.port = port
			except bt.btcommon.BluetoothError as e:
				sock.close()
				self.sock = None
			finally:
				self.cancel()