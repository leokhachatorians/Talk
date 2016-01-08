import tkinter as tk
from tkinter import filedialog
import tkinter.scrolledtext as tkScrollText
from tkinter import messagebox
import bluetooth as bt
from .modals.connect_modal import ConnectToServerWindow
from .modals.host_server_modal import HostServerWindow
import base64
import codecs
import queue

class BlueToothClient():
    def __init__(self, root, message_queue, end_gui, start_message_awaiting,
        end_bluetooth_connection):
    """
    This is the GUI class which provides the funtionality of both creating a host server to
    await for any incomming connecitons, as well as the client which attempts to connect to a host.

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

        # Sockets
        self.sock = None
        self.server = None

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

    def close_server(self):
        """
        Close our server socket and set it to none
        """
        self.server.close()
        self.server = None

    def close_socket(self):
        """
        Close our socket and set it to None
        """
        self.sock.close()
        self.sock = None

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

    def check_if_not_empty_message(self):
        """
        Determine whether or not the user is attempting to send
        a text message with no content. Used before acutally allowing data
        to be sent.

        Returns
        -------
        bool
            If there is text in the chat_send box, return true.
        """
        if self.chat_send.get():
            return True

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
            ('JPEG', '*.jpg'),
            ('PNG','*.png'),
            ('BMP','*.bmp')))
        return path_to_image 

    def send_image_workflow(self):
        """
        The main workflow needed to check if the image is compatiable with Tkinter,
        catch any raised exceptions when the user just enters and exits the file dialog,
        and actually send the image.

        We don't have to worry about if the image actually exists since Tkinter takes care
        of that for us by default within the filedialog widget.
        """
        path_to_image = self.open_image_selection_dialog()
        try:
            data = self.image_to_b64_data(path_to_image)
            self.b64_data_to_image(data)
            self.send_image(data)
            self.display_message('You:')
            self.display_image(path_to_image)
        except tk.TclError:
            self.display_message_box('showerror', 'Error', 'Invalid Image')
        except FileNotFoundError:
            pass

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

    def image_to_b64_data(self, path_to_image):
        """
        Given an image path, write the data in a base64 endcoded codec
        and return the data

        Parameters
        ----------
        path_to_image : string
            The directory path of our image file

        Returns
        -------
        data : base64 encoded bytes
            Our imagefile converted into base64 bytes

        """
        with open(path_to_image, 'rb') as img:
            data = base64.b64encode(img.read())
        return data

    def b64_data_to_image(self, data):
        """
        Write the encoded data into a .gif file.
        Once written, check to see if the file is compatible

        Parameters
        ----------
        data : base64_endcoded data
            The binary image data
        """
        with open('temp.gif', 'wb') as f:       
            f.write(codecs.decode(data, 'base64_codec'))
        self.check_if_valid_image()

    def check_if_valid_image(self):
        """
        Check to see if the image in question is compatible
        with tkinter.

        Raises
        ------
        TclError
            If the image is not compatible
        """
        try:
            image = tk.PhotoImage(file='temp.gif')
        except tk.TclError:
            raise

    def discover_nearby_devices(self):
        """
        Scan for any nearby devices and display their address. If nothing was found,
        display an error message stating as such.
        """
        self.display_message('Searching for nearby devices...')
        devices = bt.discover_devices()
        if devices:
            self.display_message('Found the following devices: ')
            for device in devices:
                self.display_message('{0}', device)
        else:
            self.display_message_box('showerror', 'Error', 'Unable to find any devices')

    def send_message(self, event=None):
        """
        If there is a current socket send a simple text message, if
        there is any BluetoothError, this means the connection was lost
        so begin the process of closing the connection on our end.

        Parameters
        ----------
        event : tkinter event
            the event thing when the users uses the <Return> key
        """
        if self.sock:
            try:
                if self.check_if_not_empty_message():
                    self.display_message('You: {}', self.chat_send.get())
                    self.sock.sendall('T' + self.chat_send.get() + '\n')
            except bt.btcommon.BluetoothError as e:
                self.display_message_box('showerror','Error','The connection was lost')
                self.close_connection()
            finally:
                self.clear_chat_send_text()

    def send_image(self, b64_data):
        """
        Send the specified image with an encoded 'I' appended at the front and
        a '\n' appended at the rear. Used to show that the data is an image and
        when the data ends respectively.

        Parameters
        ----------
        b64_data : base64_endcoded data
            The binary image data
        """
        if self.sock:
            try:
                self.sock.send('I'.encode('ascii') + b64_data + '\n'.encode('ascii'))
            except bt.btcommon.BluetoothError as e:
                print(e)

    def display_received_data(self, data):
        """
        Determine what sort of message we have received by checking the first
        byte. Depending on what value appended prior the sending of the data,
        there will be further steps in order to correctly display the message;
        if it's an image vs a file vs a text vs etc.

        Parameters
        ----------
        data : bytes 
            bytes data which was received from our receiving socket.
        """
        the_type = int(data[0])
        data = data[1:]
        if the_type == 84:
            self.display_message('Them: {}',data.decode('utf-8').rstrip('\n'))
        else:
            self.b64_data_to_image(data)
            self.display_message('Them:')
            self.display_image('temp.gif')

    def close_connection(self):
        """
        Close the current BlueTooth connection.

        If there is a current socket, begin the process of closing off
        all open connections. Catch errors depending if its a client or a
        server we are closing the connection for.
        
        If not, display a message stating that we do not have anything
        currently open.
        """
        if self.sock:
            self.end_bluetooth_connection()
            try:
                self.close_server()
            except AttributeError: # Not a server but a client
                pass
            finally:
                self.close_socket()
                self.display_message('Closed connection')
                self.disable_send_button()
        else:
            self.display_message_box('showinfo','No Connection', 'No connection to close')

    def create_host_server_window(self):
        """
        Create the 'host the server' modal.

        If we succesfully accept an incoming connection, set up the internals
        and wait for incoming messages.

        If we do not get any connections before our timeout value, display
        an error message stating as such.
        """
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


    def check_message_queue(self):
        """
        When called will check to determine if there is anything within our queue.
        If there is, we pull out the data and determine how to display it, unless
        the queue is empty, then it stops.
        """
        while self.message_queue.qsize():
            try:
                data = self.message_queue.get()
                self.display_received_data(data)
            except queue.Empty:
                pass