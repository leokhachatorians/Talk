import tkinter as tk
import threading
import queue
import sys
import time
from classes.bluetooth_gui import BlueToothClient

class ThreadedClient():
    def __init__(self, master):
        self.master = master
        self.message_queue = queue.Queue()

        self.thread_stop = threading.Event()
        self.running = True
        self.all_data = []
        self.got_length = False

        self.gui = BlueToothClient(master, self.message_queue, self.end_command, self.start_message_awaiting)
        self.periodic_call()

    def start_message_awaiting(self):
        self.thread_stop.clear()
        self.await_messages = threading.Thread(target=self.await_messages_thread,
            daemon=True)
        self.await_messages.start()

    def stop_threads(self):
        try:
            sys.exit(1)
        except Exception as e:
            print(e)

    def periodic_call(self):
        self.gui.check_message_queue()
        if not self.running:
            self.stop_threads()
        else:
            self.master.after(100, self.periodic_call)

    # def await_messages_thread(self):

        # while True:
        #     total_data = []
        #     print('total data')
        #     print(total_data)
        #     begin = time.time()
        #     if total_data and time.time() - begin > 2:
        #         break
        #     elif time.time() - begin > 2*2:
        #         break

        #     try:
        #         data = self.gui.sock.recv(8192)
        #         print(data)
        #         if data:
        #             total_data.append(data)
        #             print('got data')
        #             print(total_data)
        #             begin = time.time()
        #         else:
        #             time.sleep(0.1)
        #     except:
        #         pass

        # put_data = ''.join(total_data)
        # self.message_queue.put(put_data)


    def await_messages_thread(self):
        while self.running:
            more_data = True
            buff = b''
            while more_data:
                data = self.gui.sock.recv(8192)
                if '\n'.encode('ascii') in data:
                    more_data = False
                    buff += data
                else:
                    buff += data
            try:
                #print(buff)
                self.message_queue.put(buff)
            except AttributeError:
                pass

    def end_command(self):
        self.running = False