import tkinter as tk
from .modals.connect_modal import ConnectToServerWindow
from .modals.host_server_modal import HostServerWindow

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
        self.bt_menu.add_command(label='Close Connection',
            command=self.close_connection)
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

        # Rightclick Menu
        self.make_right_click_menu(self.root)

        # Open Window Checks
        self.host_server_window_is_open = False
        self.connect_to_window_is_open = False

    def delete_child_window(self, window):
        window.destroy()

    def disable_chat_display_state(self):
        self.chat_display.configure(state='disabled')

    def enable_chat_display_state(self):
        self.chat_display.configure(state='normal')

    def update_chat_display(self):
        self.chat_display.update_idletasks()

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

    def paste_over_selection(self, event=None):
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
            command=self.paste_over_selection)
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
        self.update_chat_display()
        self.disable_chat_display_state()

    def discover_nearby_devices(self):
        self.display_message('Searching for nearby devices...')
        devices = bt.discover_devices()
        if devices:
            self.display_message('Found the following devices: ')
            for device in devices:
                self.display_message('{0}', device)
        else:
            self.display_message('Unable to find any devices')

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

    def close_connection(self):
        if self.sock:
            self.sock = None
            self.server = None
            self.display_message('Closed connection')
        else:
            self.display_message('No connection to close')

    def create_host_server_window(self):
        try:
            host_server = HostServerWindow(self.root, title='Host a Server')
            if host_server.sock:
                self.sock = host_server.sock
                self.server = host_server.server
                client_info = host_server.client_info

                self.display_message('Connected with: {0}',client_info)

                self.enable_send_button()
                self.start_message_awaiting()
            else:
                self.display_message(host_server.error_message)
        except Exception as e:
            pass

    def create_connect_to_window(self):
        try:
            connection = ConnectToServerWindow(self.root, title='Connect')
            if connection.sock:
                self.sock = connection.sock
                self.display_message('Connection Succesful')
                self.enable_send_button()
                self.start_message_awaiting()
            else:
                self.display_message('Connection Failed')
        except Exception as e:
            pass