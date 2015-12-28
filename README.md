# pbChat

## What is it?
pbChat is a lightweight BlueTooth chat application built entirely out of Python3 and tkinter. 

## Things Left To Do
* ~~Create ability to host a server~~
* ~~Implement discovering/inquiring~~
* ~~Better notifications on internal processes~~
* Breakdown and modularize various GUI widgets/windows/etc
* Better chat (images etc)
* File transfer
* Actually add documentation
* Anything else I can think of

## What You Need
* python3
* pybluez

## How To Run
* run 'python bluetooth_gui.py' on two seperate computers
* one computer creates a host server and the other connects to it via its BlueTooth address and port
* commence chatting

## Known Issues
* ~~Thread lockup when attempting to exit, sometimes.~~ hehe daemon threads
* GUI Lockup when connecting/hosting/etc
