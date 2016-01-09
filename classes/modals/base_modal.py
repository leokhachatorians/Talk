import tkinter as tk

class ModalWindow(tk.Toplevel):
	"""
	The basic modal window which all others are inherited from.
	"""
	def __init__(self, parent, title=None):
		tk.Toplevel.__init__(self, parent)
		self.transient(parent)
		self.sock = None
		self.server = None
		self.error_message = None

		if title:
			self.title(title)

		self.parent = parent
		self.result = None

		body = tk.Frame(self)

		self.initial_focus = self.body(body)
		body.pack(padx=5,pady=5)

		self.button_box()

		self.grab_set()

		if not self.initial_focus:
			self.initial_focus = self

		self.protocol('WM_DELETE_WINDOW', self.cancel)
		self.geometry("+%d+%d" % (
			parent.winfo_rootx()+50,
			parent.winfo_rooty()+50))

		self.initial_focus.focus_set()
		self.wait_window(self)


	def body(self, master):
		"""
		Sole purpose is to be overriden.
		"""
		pass

	def button_box(self):
		"""
		Main button box format which is inherited by the connect and host modals.
		"""
		box = tk.Frame(self)

		ok_button = tk.Button(box, text="Ok", width=10,
			command=self.ok,
			default=tk.ACTIVE)
		ok_button.pack(side=tk.LEFT, padx=5,pady=5)
		cancel_button = tk.Button(box, text="Cancel", width=10,
			command=self.cancel)
		cancel_button.pack(side=tk.LEFT, padx=5, pady=5)
		self.bind("<Escape>", self.cancel)

		box.pack()

	def cancel(self, event=None):
		"""
		Destroys modal when called
		"""
		self.destroy()
