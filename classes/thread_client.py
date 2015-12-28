import tkinter as tk
import threading
import queue
import sys
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

    def await_messages_thread(self):
        while self.running:
            try:
                self.message_queue.put(self.gui.sock.recv(1024))
            except AttributeError:
                pass

    def end_command(self):
        self.running = False