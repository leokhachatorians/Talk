# pbChat

## What is it?
pbChat is a lightweight BlueTooth chat application

## Things Left To Do
* ~~Create ability to host a server~~
* ~~Implement discovering/inquiring~~
* ~~Better notifications on internal processes~~
* Better chat
* Actually add documentation
* Anything else I can think of

## What You Need
* python3 (python2, might work but ain't mah problem)
* pybluez

## How To Run
* first create a bluetooth server by running 'python basic_server.py'
* then run 'python bluetooth_gui.py' and connect to it with via the servers address and port number
* commence chatting

## Known Issues
* ~~Thread lockup when attempting to exit, sometimes.~~ hehe daemon threads
* GUI Lockup when connecting/hosting/etc
