import tkinter as tk
from tkinter import filedialog
from classes.bluetooth_backend import BluetoothBackend
from classes.gui_backend import GUIBackend
import tkinter.scrolledtext as tkScrollText
from tkinter import messagebox
from .modals.connect_modal import ConnectToServerWindow
from .modals.host_server_modal import HostServerWindow

class BluetoothChatGUI(BluetoothBackend,GUIBackend):
    def __init__(self, root, message_queue, end_gui, start_message_awaiting,
        end_bluetooth_connection):
        """
        This is the GUI class which provides the main interface between the client and
        the backend. It's functions consist of things which directly modify the GUI Without
        dealing with Bluetooth or checking data transmited to and from the connections.

        Parameters
        ----------
        root : tk root object
            This is the passed along tk root thing
        message_queue : a queue.queue
            Passed in queue which we check periodically for data
        end_gui : a function
            When called, will notify the working thread to exit out of the thread
        start_message_awaiting : a function
            When called, will notify the working thread that its ok to start
            the process of accepting any incoming data
        end_bluetooth_connection : a function
            When called, notifies the working thread that the Bluetooth Connection
            will be shut down, and that there is to be no more checking for messages.
        """
        self.root = root
        self.message_queue = message_queue
        self.end_gui = end_gui
        self.start_message_awaiting = start_message_awaiting
        self.end_bluetooth_connection = end_bluetooth_connection

        # Menu Bar
        self.menubar = tk.Menu(root)
        self.root.config(menu=self.menubar)

        # File Tab
        self.file_menu = tk.Menu(self.menubar, tearoff=0)
        self.file_menu.add_command(label='Exit',command=self.end_gui)

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
            command=self.send_image_workflow)
        self.chat_menu.add_command(label='Send File',
            command=self.send_file_workflow)
        self.chat_menu.add_command(label='Clear Chat',
            command=self.clear_chat_display)

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

    def disable_chat_display_state(self):
        """
        Prevents the chat display widget from being modified.
        """
        self.chat_display.configure(state='disabled')

    def enable_chat_display_state(self):
        """
        Enables the chat display widget to be modified.
        """
        self.chat_display.configure(state='normal')

    def update_chat_display(self):
        """
        When called will force our chat display widget to refresh any changes
        which may be waiting to be shown. If we don't call this, then certain
        things may not be shown in the order or at the time we want them to be
        shown.
        """
        self.chat_display.update_idletasks()

    def enable_send_button(self):
        """
        Enables the send button to be used
        """
        self.send_button.config(state="normal")

    def disable_send_button(self):
        """
        Disables the send button from being used
        """
        self.send_button.config(state="disabled")

    def clear_chat_send_text(self):
        """
        Clears any text within our chat send widget
        """
        self.chat_send.delete(0, 'end')

    def clear_chat_display(self):
        """
        Clears all text and images from our chat display widget.
        """
        self.enable_chat_display_state()
        self.chat_display.delete('1.0', 'end')
        self.disable_chat_display_state()

    def right_click_menu_functionality(self, event, menu):
        """
        What actually allows our right click menu to 'pop up'.

        Parameters
        ----------
        event : tkinter event
            The event is what we require in order to capture the actual mousebind.
            Without it, it won't work
        menu : tkinter menu object
            This is the menu we want to have displayed when called
        """
        menu.tk_popup(event.x_root,
            event.y_root)

    def select_all_text(self, event):
        """
        Function we use when we bind 'Ctrl+A'; it selects all the text.

        Parameters
        ----------
        event : tkinter event
            The event is what we require in order to capture the actual keybind.
            Without it, it won't work.
        """
        event.widget.selection_range("0","end")

    def display_message_box(self, the_type, title, text):
        """
        Create and display a tkinter messagebox via 'messagebox',
        a builtin tkinter module.

        'messagebox.thetype(title, text)'

        Parameters
        ----------
        the_type : string
            The type of messagebox we want to have display
        title : string
            The title we want the message box to have
        text : string
            The text we want the message box to dispay
        """
        getattr(messagebox, the_type)(title, text)

    def display_decision_box(self, data):
        file_name_and_type = data[1] + data[2]
        file_size = data[3]
        decision = messagebox.askyesno('Incoming File',
                    'Would you like to accept\n{0}\nSize: {1}?'.format(
                        file_name_and_type, file_size))
        return decision

    def open_image_selection_dialog(self):
        """
        Open a filedialog with a given set of options to get the path of the
        selected image the user wishes to send.

        Note that there is no catching or preventing of any files which may not
        exist, the actual widget does that work for us out of the box.

        Returns
        -------
        path_to_image : string:
            The path to our image, will be an empty string if user does
            not select anything
        """
        path_to_image = filedialog.askopenfilename(filetypes=(('GIF','*.gif'),
            ('JPEG', '*.jpg;*.jpeg'),
            ('PNG','*.png'),
            ('BMP','*.bmp'),
            ("All Files","*.*")))
        return path_to_image 

    def open_file_selection_dialog(self):
        file_selection = filedialog.askopenfilename(filetypes=(
                ("Text Files", "*.txt;"),
                ("PDF Files", "*.pdf"),
                ("Microsoft Word Files","*.doc;*.docx;*.dot;"),
                ("Rich Text Format","*.rtf"),
                ("Python Files","*.py"),
                ("C Files","*.c"),
                ("HTML Files","*.htm;*.html"),
                ("JavaScript Files","*.js"),
                ("All Files","*.*")))
        return file_selection

    def paste_over_selection(self, event=None):
        """
        Replicate the function of removing text when we highlight and paste into it.

        Parameters
        ----------
        event : tkinter event
            Used as a binding for when we use Ctrl+v to perform the action
        """
        try:
            text_to_paste = self.root.clipboard_get()
            start = self.root.focus_get().index('sel.first')
            end = self.root.focus_get().index('sel.last')
            self.root.focus_get().delete(start, end)
        except tk.TclError as e:
            pass
        finally:
            self.root.focus_get().insert(tk.INSERT, text_to_paste)

    def make_right_click_menu(self, window):
        """
        Create the right click menu for our given window. Also binds our right
        click button to display the menu.

        Parameters
        ----------
        window : tk window object
            Where our rightclick menu should be displayed and functional
        """
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

    def display_message(self, message, data=None):
        """
        Display a message within our chat display widget.

        Parameters
        ----------
        message : string
            The message to be displayed
        data : string, optional
            If there is any additonal information we want to display within
            our message which we couldn't do otherwise.
        """
        self.enable_chat_display_state()
        if data:
            self.chat_display.insert('end', message.format(data) + '\n')
        else:
            self.chat_display.insert('end', message + '\n')
        self.chat_display.see('end')
        self.update_chat_display()
        self.disable_chat_display_state()

    def display_image(self, path_to_image):
        """
        Given an image path, display the image within our chat display widget.

        Parameters
        ----------
        path_to_image : string
            The directory path of our image file
        """
        image = tk.PhotoImage(file=path_to_image)
        l = tk.Label(image=image)
        l.image = image
        self.enable_chat_display_state()
        self.chat_display.image_create('end',image=image)
        self.display_message('\n')
        self.chat_display.see('end')
        self.disable_chat_display_state()

    def create_host_server_window(self):
        """
        Create the 'host the server' modal.

        If we succesfully accept an incoming connection, set up the internals
        and wait for incoming messages.

        If we do not get any connections before our timeout value, display
        an error message stating as such.
        """
        if self.sock:
            self.display_message_box('showerror','Already Connected','Close your current connection before attempting to host a connection.')
        else:
            host_server = HostServerWindow(self.root, title='Host a Server')
            if host_server.sock:
                self.sock = host_server.sock
                self.server = host_server.server
                client_info = host_server.client_info
                self.display_message('Connected with: {0}',client_info)
                self.enable_send_button()
                self.chat_send.focus_set()
                self.start_message_awaiting()
            elif host_server.error_message:
                self.display_message_box('showerror', 'Error', host_server.error_message)

    def create_connect_to_window(self):
        """
        Create the 'connect to server' modal.

        If we succesfully connect to a server, set up the internals and begin
        waiting for incoming messages.

        If the user attempts to connect but we do not receive a valid socket before
        the timeout, or really any BlueTooth related error, display a generic error message.
        """
        if self.sock:
            self.display_message_box('showerror','Already Connected','Close your current connection before attempting to connect to another server.')
        else:
            connection = ConnectToServerWindow(self.root, title='Connect')
            if connection.sock:
                self.sock = connection.sock
                address, port = connection.address, connection.port
                self.display_message('Connected Succesfully to {0} on port {1}'.format(address, port))
                self.enable_send_button()
                self.chat_send.focus_set()
                self.start_message_awaiting()
            elif connection.error_message:
                self.display_message_box('showerror', 'Error', 'Connection Failed')