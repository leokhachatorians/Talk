import tkinter as tk

class ModalWindow(tk.Toplevel):
	def __init__(self, parent, title=None):
		tk.Toplevel.__init__(self, parent)
		#self.transient(parent)

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

	def make_right_click_menu(self, window):
		print('sss')
		right_click_menu = tk.Menu(window, tearoff=0)
		right_click_menu.add_command(label='Copy',
			accelerator='Ctrl+C',
			command=lambda: window.focus_get().event_generate('<<Copy>>'))
		right_click_menu.add_command(label='Cut',
			command=lambda: window.focus_get().event_generate('<<Cut>>'))
		right_click_menu.add_command(label='Paste',
			accelerator='Ctrl+V',
			command=self.paste_over_selection)
		right_click_menu.add_command(label='Delete',
			command=lambda: window.focus_get().event_generate('<<Clear>>'))

		window.bind('<Button 3>',
			lambda event, menu=right_click_menu: self.right_click_menu_functionality(event,menu))       