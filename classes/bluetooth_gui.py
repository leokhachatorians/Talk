import tkinter as tk
from tkinter import filedialog
import tkinter.scrolledtext as tkScrollText
import bluetooth as bt
from .modals.connect_modal import ConnectToServerWindow
from .modals.host_server_modal import HostServerWindow
import base64
import codecs
import queue
import time
import struct

class BlueToothClient():
    def __init__(self, root, message_queue, end_command, start_message_awaiting):
        self.root = root
        self.message_queue = message_queue
        self.end_command = end_command
        self.start_message_awaiting = start_message_awaiting

        # Menu Bar
        self.menubar = tk.Menu(root)
        self.root.config(menu=self.menubar)

        # File Tab
        self.file_menu = tk.Menu(self.menubar, tearoff=0)
        self.file_menu.add_command(label='Exit',command=self.end_command)

        # BlueTooth Tab
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

        # Chat Tab
        self.chat_menu = tk.Menu(self.menubar, tearoff=0)
        self.chat_menu.add_command(label='Send Image',
            command=self.open_file_dialog)
        self.chat_menu.add_command(label='Clear Chat')

        # Settings Tab
        self.settings_menu = tk.Menu(self.menubar, tearoff=0)
        self.settings_menu.add_command(label='Font')
        self.settings_menu.add_command(label='Misc')

        # Add Tabs to Menu
        self.menubar.add_cascade(label='File',menu=self.file_menu)
        self.menubar.add_cascade(label='BlueTooth',menu=self.bt_menu)
        self.menubar.add_cascade(label='Chat', menu=self.chat_menu)
        self.menubar.add_cascade(label='Settings', menu=self.settings_menu)

        # Key Binds
        self.root.bind('<Return>', self.send_message)
        self.root.bind_class("Entry","<Control-v>", self.paste_over_selection)
        self.root.bind_class("Entry","<Control-a>", self.select_all_text)

        # Sockets
        self.sock = None
        self.server = None
        self.total_message = []

        # Chat Receive Display
        self.chat_display = tkScrollText.ScrolledText(root)
        self.chat_display.configure(state='disabled',font='helvetica 14')
        self.chat_display.pack(ipady=3)
        self.chat_display.grid(row=0, 
            column=0, 
            rowspan=10,
            columnspan=10)
        self.chat_display.bind("<1>", lambda event: self.chat_display.focus_set())

        # Chat Send Display
        self.chat_send = tk.Entry(root)
        self.chat_send.pack(ipady=10)
        self.chat_send.grid(row=11,
            column=0,
            columnspan=9,
            sticky=tk.W+tk.E+tk.N+tk.S)
        self.chat_send.focus_set()

        # Send Button
        self.send_button = tk.Button(root, text="Enter", command=self.send_message, state="disabled")
        self.send_button.grid(row=11,
            column=9,
            sticky=tk.W+tk.E+tk.N+tk.S)

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
        menu.tk_popup(event.x_root,
            event.y_root)

    def select_all_text(self, event):
        event.widget.selection_range("0","end")

    def send_message_size(self, the_message):
        message_size = str(len(the_message))
        #size_in_binary = struct.pack('I', message_size)
        self.sock.sendall(message_size)

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

    def open_file_dialog(self):
        path_to_image = filedialog.askopenfilename(filetypes=(('GIF','*.gif'),
            ('JPEG', '*.jpg'),
            ('PNG','*.png'),
            ('BMP','*.bmp')))
        data = self.image_to_b64_data(path_to_image)
        self.send_image(data)
        self.display_message('You:')
        self.display_image(path_to_image)

    def display_message(self, message, data=None):
        self.enable_chat_display_state()
        if data:
            self.chat_display.insert('end', message.format(data) + '\n')
        else:
            self.chat_display.insert('end', message + '\n')
        self.update_chat_display()
        self.disable_chat_display_state()

    def display_image(self, path_to_image):
        image = tk.PhotoImage(file=path_to_image)
        l = tk.Label(image=image)
        l.image = image

        self.enable_chat_display_state()
        self.chat_display.image_create('end',image=image)
        self.display_message('\n')
        self.disable_chat_display_state()

    def image_to_b64_data(self, photo):
        with open(photo, 'rb') as img:
            data = base64.b64encode(img.read())
        return data

    def b64_data_to_image(self, data):
        with open('temp.gif', 'wb') as f:
            f.write(codecs.decode(data, 'base64_codec'))

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
                    self.sock.sendall(self.chat_send.get() + '\n')
            except bt.btcommon.BluetoothError as e:
                self.display_message('The connection was lost ')
                self.sock = None
                self.server = None
                self.disable_send_button()
            finally:
                self.clear_chat_send_text()

    def send_image(self, b64_data, event=None):
        if self.sock:
            try:
                self.sock.send(b64_data + '\n'.encode('ascii'))
            except bt.btcommon.BluetoothError as e:
                print(e)

    def check_message_queue(self):
        while self.message_queue.qsize():
            data = self.message_queue.get()
            try:
                self.enable_chat_display_state()
                self.chat_display.insert('end', 'Them:\n')
                self.disable_chat_display_state()
                self.b64_data_to_image(data)
                self.display_image('temp.gif')
                self.update_chat_display()
            except Exception:
                self.display_message('Them: {}',data.decode('utf-8').rstrip('\n'))
            except queue.Empty:
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