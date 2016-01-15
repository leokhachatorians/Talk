import bluetooth as bt

class BluetoothBackend():
    """
    This is a class which our GUI inherits from. It's main purpose is to deal
    with really anything that involves the Bluetooth network. Things like creating, 
    closing sockets, discovering devices, and sending data over sockets.

    Functions which deal with manipulation of data prior to socket interaction will
    not be housed within this class.

    Note however that there are multiple instances of calling methods which
    adjust or modify the GUI. Still not sure if those sections are appropirate
    or whether they should be seperated entirely.
    """
    sock = None
    server = None

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
            except bt.btcommon.BluetoothError:
                print(e)

    def send_incoming_file_alert(self, file_name, file_type, file_size, file_path):
        if self.sock:
            file_information = ('\t' + file_name + '\t' + file_type + '\t' + file_size + '\t' + file_path).encode('ascii')
            try:
                self.sock.send('?'.encode('ascii') + file_information + '\n'.encode('ascii'))
            except bt.btcommon.BluetoothError:
                self.display_message_box('showerror','Error','The connection was lost')
                self.close_connection()

    def send_accepting_file_notification(self, file_path):
        if self.sock:
            try:
                self.sock.send(('A').encode('ascii') + file_path + '\n'.encode('ascii'))
            except bt.btcommon.BluetoothError:
                self.display_message_box('showerror','Error','The connection was lost')
                self.close_connection()

    def send_rejecting_file_notification(self):
        if self.sock:
            try:
                self.sock.send(('R' + '\n').encode('ascii'))
            except bt.btcommon.BluetoothError:
                self.display_message_box('showerror','Error','The connection was lost')
                self.close_connection()

    def send_file(self, data, file_name, file_type):
        if self.sock:
            file_information = ('\t' + file_name + '\t' + file_type + '\t').encode('ascii')
            try:
                self.sock.send('F'.encode('ascii') + file_information + data + '\n'.encode('ascii'))
            except bt.btcommon.BluetoothError:
                self.display_message_box('showerror','Error','The connection was lost')
                self.close_connection()

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