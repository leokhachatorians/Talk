import base64
import codecs
import tkinter as tk
import os

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
        it_is_an_image = self.check_if_actually_image(path_to_image)
        if self.sock:
            if it_is_an_image:
                try:
                    data = self.convert_to_b64_data(path_to_image)
                    self.check_if_valid_image()
                    self.send_image(data)
                    self.display_message('You:')
                    self.display_image(path_to_image)
                except tk.TclError:
                    self.display_message_box('showerror', 'Error', 'Invalid Image')
                except FileNotFoundError:
                    pass
            else:
                self.display_message_box('showerror', 'Not an Image',
                 'File selected was not an image. If you want to send a file use \'Send File\'')
        else:
            self.display_message_box('showerror', 'No Connection',
             'You need to have an active Bluetooth connection first.')

    def check_if_actually_image(self, file_path):
        """
        Check to see if the file selected to send over chat is actually an image.

        Parameters
        ----------
        file_path : string
            The full file path of the image in question

        Returns
        -------
            If the file ending is in the acceptable file endings, return True.
        """
        file_ending = '.' + file_path.split('/')[-1].split('.')[1]
        image_path_endings = ['.jpg','.gif','.png','.bmp','.jpeg']

        if file_ending in image_path_endings:
            return True

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

    def prepare_incoming_file_alert(self):
        if self.sock:
            file_path = self.open_file_selection_dialog()
            file_information = self.prepare_file_information(file_path)
            file_name = file_information[0]
            file_type = file_information[1]
            file_size = file_information[2]

            self.send_incoming_file_alert(file_name, file_type, file_size, file_path)
        else:
            self.display_message_box('showerror', 'No Connection',
             'You need to have an active Bluetooth connection first.')

    def prepare_to_send_file(self, file_path):
        if self.sock:
            file_information = self.prepare_file_information(file_path)
            file_name = file_information[0]
            file_type = file_information[1]

            data = self.convert_to_b64_data(file_path)
            self.send_file(data, file_name, file_type)

    def prepare_file_information(self, file_path):
        file_name = file_path.split('/')[-1].split('.')[0]
        file_ending = '.' + file_path.split('/')[-1].split('.')[1]
        unformatted_file_size = int(str(os.stat(file_path).st_size).strip('L'))
        formated_file_size = self.size_formater(unformatted_file_size)

        return [file_name, file_ending, formated_file_size, file_path]

    def size_formater(self, size):
        for unit in ['bytes','kB','MB','GB','TB','PB']:
            if abs(size) < 1024.0:
                return "%3.1f %s" % (size, unit)
            size /= 1024.0

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

    def convert_to_b64_data(self, full_file_path):
        """
        Given an image path, write the data in a base64 endcoded codec
        and return the data

        Parameters
        ----------
        full_file_path : string
            The directory path of our file

        Returns
        -------
        data : base64 encoded bytes
            Our file converted into base64 bytes

        """
        with open(full_file_path, 'rb') as img:
            data = base64.b64encode(img.read())
        return data

    def convert_from_b64_data(self, data, chat_image=False):
        """
        Convert the base64 encoded data into binary data.

        If the data is meant to be displayed in the chat window, save it as 
        'temp.gif' so that we may display it. Otherwise, save the file with the same
        name and type as it was sent.

        Parameters
        ----------
        data : The base64 encoded data
            The encoded data we wish to either display or save
        chat_image : Bool
            Set True to display the image and False to save the file as is.
        """
        if chat_image:
            with open('temp.gif', 'wb') as the_image:
                the_image.write(codecs.decode(data, 'base64_codec'))
        else:
            file_name = data[1]
            file_type = data[2]
            data = data[3]
            with open(file_name + file_type, 'wb') as the_file:
                the_file.write(codecs.decode(data, 'base64_codec'))
        
    def manage_received_data(self, data):
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
        the_message_type = int(data[0])
        data = data[1:]

        # split the data into a list to peice together the file
        # used only for sending files
        seperated_data = data.split('\t'.encode('ascii'))

        if the_message_type == 84: # regular message
            self.display_message('Them: {}',data.decode('utf-8'))
        elif the_message_type == 70: # file message
            self.convert_from_b64_data(seperated_data)
        elif the_message_type == 63: # accept/decline file message
            result = self.display_decision_box(seperated_data)
            if result:
                self.send_accepting_file_notification(seperated_data[4])
            else:
                self.send_rejecting_file_notification()
        elif the_message_type == 65: # User accepted our file message
            self.prepare_to_send_file(data.decode('utf-8'))
        elif the_message_type == 82: # user declined our file message
            self.display_message_box('showerror','Refused','The file was refused.')
        else: # chat image message
            self.convert_from_b64_data(data, chat_image=True)
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
                self.manage_received_data(data)
            except queue.Empty:
                pass