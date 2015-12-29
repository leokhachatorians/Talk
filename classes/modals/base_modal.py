import tkinter as tk

class ModalWindow(tk.Toplevel):
	def __init__(self, parent, title=None):
		tk.Toplevel.__init__(self, parent)
		self.transient(parent)

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
		pass

	def button_box(self):
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
		# put focus back to the parent window
		self.parent.focus_set()
		self.destroy()
		return 'a'