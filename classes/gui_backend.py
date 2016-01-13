import base64
import codecs
import tkinter as tk
from tkinter import filedialog

class GUIBackend():
    """This is a class which our GUI inherits from. 

    Want the majority of these functions to be primarily functions which do NOT 
    have a direct impact on the GUI.

    Think of this class as the workhouse for functions which do work involving data.
    They will often call upon the GUI to do certain things pertaining to the data, 
    but never things which have no purpose but adjusting the way things work on a GUI level.

    Any things which involve direct communication or manipulation of sockets will also not be
    housed here. But if it involves preparing the data PRIOR to socket involvement it is acceptable.
    """

    def send_image_workflow(self):
        """
        The main workflow needed to check if the image is compatiable with Tkinter,
        catch any raised exceptions when the user just enters and exits the file dialog,
        and actually send the image.

        We don't have to worry about if the image actually exists since Tkinter takes care
        of that for us by default within the filedialog widget.

        We also make sure that any non-image files get prevented from being sent and
        display a warning message stating as such.
        """
        path_to_image = self.open_image_selection_dialog()
        file_type = self.check_file_type(path_to_image)
        if file_type == 'Image':
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

    def check_file_type(self, file_path):
        file_path_ending = file_path[-3:]
        image_path_endings = ['jpg','gif','png','bmp','jpeg']
        if file_path_ending in image_path_endings:
            return 'Image'
        else:
            return 'File'

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

    def send_file(self):
        if self.sock:
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
        else:
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