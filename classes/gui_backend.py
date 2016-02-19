import base64
import codecs
import tkinter as tk
import os
import queue
from PIL import Image
from utils.wrapper import check_bluetooth

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

    @check_bluetooth
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
        if it_is_an_image:
            try:
                self.convert_image_to_gif(path_to_image)
                data = self.convert_to_b64_data('temp.gif')
                self.send_image(data)
                self.display_message('You:')
                self.display_image('temp.gif')
            except Exception as e:
                self.display_message_box('showerror', 'Error', 'Invalid Image')

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
        try:
            file_ending = '.' + file_path.split('/')[-1].split('.')[1]
        except IndexError:
            pass

        image_path_endings = ['.jpg','.gif','.png','.bmp','.jpeg']

        if file_ending in image_path_endings:
            return True
        else:
            self.display_message_box('showerror', 'Not an Image',
                'File selected was not an image. If you want to send a file use \'Send File\'')

    def convert_image_to_gif(self, path):
        im = Image.open(path)
        im.save('temp.gif','GIF')

    @check_bluetooth
    def prepare_incoming_file_alert(self):
        file_path = self.open_file_selection_dialog()
        info = self.prepare_file_information(file_path)
        file_name, file_size = info[0], info[1]

        self.send_incoming_file_alert(file_name, file_size, file_path)

    def prepare_to_send_file(self, file_path):
        info = self.prepare_file_information(file_path)
        file_name = info[0]
        data = self.convert_to_b64_data(file_path)
        self.send_file(data, file_name)

    def prepare_file_information(self, file_path):
        file_name = file_path.split('/')[-1]
        unformatted_file_size = int(str(os.stat(file_path).st_size).strip('L'))
        formated_file_size = self.size_formater(unformatted_file_size)

        return (file_name, formated_file_size, file_path)

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

    def convert_to_b64_data(self, file_path):
        """
        Given a file path, write the data in a base64 endcoded codec
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
        with open(file_path, 'rb') as date:
            encoded_data = base64.b64encode(date.read())
        return encoded_data

    def convert_from_b64_and_save_to_disk(self, data, chat_image=False):
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
            file_name = 'temp.gif'
        else:
            file_name, data = data[1], data[2]
            file_name = self.rename_file_if_already_exists(file_name)
        with open(file_name, 'wb') as the_file:
            the_file.write(codecs.decode(data, 'base64_codec'))

    def rename_file_if_already_exists(self, file_name):
        """
        When receiving a file, check to see if the file already exists
        within the directory. If it does, append '(Copy i)', where i is the
        ith copy of the file, to the end of the file name, before the extension.

        Regardless if the filename exists in the directory, return 'copy',
        as it will either be the same filename or the new one anyway.

        Parameters
        ----------
        file_name : string
            The file name to check

        Returns
        -------
        copy : string
            The modified/original filename we created
        """
        file_name = file_name.decode('utf8')
        copy = file_name
        count = 1
        while os.path.isfile(copy):
            copy = file_name.split('.')
            copy.insert(1, '.')
            copy.insert(1, '(Copy {0})'.format(count))
            count += 1
        copy = ''.join(copy)
        return copy
        
    def manage_received_data(self, data):
        """
        Determine what sort of message we have received by checking the first
        byte. Depending on what value appended prior the sending of the data,
        there will be further steps in order to correctly display the message;
        if it's an image vs a file vs a text vs etc.

        63 == incoming file alert message
        65 == user accepted file
        69 == user left chat
        70 == file message
        73 == image message
        82 == user rejected file
        84 == regular text message
        
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

        if the_message_type == 63:
            result = self.display_decision_box(seperated_data)
            if result:
                self.send_accepting_file_notification(seperated_data[3])
            else:
                self.send_rejecting_file_notification()
        elif the_message_type == 65:
            self.prepare_to_send_file(data.decode('utf-8'))
        elif the_message_type == 69:
            self.display_message("User has disconnected.")
            self.close_connection()
        elif the_message_type == 70:
            self.convert_from_b64_and_save_to_disk(seperated_data)
        elif the_message_type == 73:
            self.convert_from_b64_and_save_to_disk(data, chat_image=True)
            self.display_message('Them:')
            self.display_image('temp.gif')       
        elif the_message_type == 82:
            self.display_message_box('showerror','Refused','The file was refused.')
        elif the_message_type == 84:
            self.display_message('Them: {}',data.decode('utf-8'))

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