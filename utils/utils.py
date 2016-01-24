from functools import wraps

def check_bluetooth(f):
    """
    The decorator which checks for an active Bluetooth connection.

    If there is a socket, we continue on and try the function call
    unless for whatever reason there is a Bluetooth specific error,
    namely the connection being lost. If so, notify the user that
    of the lost connection and begin the process of cleanly reseting
    their open sockets.

    If there is no socket, then notify the user of such. This portion
    is more primarily used for instances of sending files or images,
    where the ability to do so is handled via the chat menu and the users
    own attempts.
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        if args[0].sock:
            try:
                f(*args,**kwargs)
            except bt.btcommon.BluetoothError:
                args[0].the_connection_was_lost()
        else:
            args[0].display_message_box('showerror', 'No Connection',
                'You need to have an active Bluetooth connection first.')
    return wrapper