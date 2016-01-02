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

    def recv_timeout(self, the_socket,timeout=1):
        #make socket non blocking
        the_socket.setblocking(0)
         
        #total data partwise in an array
        total_data=[];
        data='';
         
        #beginning time
        begin=time.time()
        while 1:
            #if you got some data, then break after timeout
            if total_data and time.time()-begin > timeout:
                break
             
            #if you got no data at all, wait a little longer, twice the timeout
            elif time.time()-begin > timeout*2:
                break
             
            #recv something
            try:
                data = the_socket.recv(8192)
                if data:
                    total_data.append(data)
                    #change the beginning time for measurement
                    begin=time.time()
               # else:
                    #sleep for sometime to indicate a gap
                    #time.sleep(0.1)
            except:
                pass
         
        #join all parts to make final string
        try:
            return total_data[0]
        except IndexError:
            return False

    def await_messages_thread(self):
        while self.running:
            data = self.gui.sock.recv(1024)
            if data:
                try:
                    # self.message_queue.put(self.gui.sock.recv(1024))
                    self.message_queue.put(data)
                except AttributeError:
                    pass
    def end_command(self):
        self.running = False