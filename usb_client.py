#!/usr/bin/env python

from socketIO_client import SocketIO, LoggingNamespace, BaseNamespace
import logging
import argparse
import subprocess

logging.getLogger('requests').setLevel(logging.WARNING)
logging.basicConfig(level=logging.DEBUG)

class UsbNamespace(BaseNamespace):

    def on_aaa_response(self, *args):
        print('on_aaa_response', args)

SOCKETIO = SocketIO('localhost', 5000)
USB_NAMESPACE = SOCKETIO.define(UsbNamespace, '/usb')
DATA = {u'server_message': u'no message'}
USB_STATE = "unknown"
SERIAL = "undetermined"


# update server with serial and 
def notify_value(*message):
    usb_values = get_usb_values()
    send_socket_message(usb_values)


def get_usb_values():

    global SERIAL, USB_STATE

    # bash command to get serial of usb drive
    get_usb_serial = "udevadm info -a -n /dev/external_usb | grep '{serial}' | head -n1"

    # run bash command and pipe output
    p = subprocess.Popen(get_usb_serial, stdout=subprocess.PIPE, shell=True)

    # read output
    usb_serial_output = p.stdout.read()

    # strip output
    SERIAL = str(usb_serial_output).strip()

    # check to see if usb/sd device is connected
    if "ATTRS{serial}" in SERIAL:
        USB_STATE = "connected"
        SERIAL = SERIAL

    else:
        USB_STATE = "no_device"
        SERIAL = "no device connected"

    return {'usb_state': USB_STATE, 'serial_value': SERIAL}


def send_socket_message(usb_values):
    global USB_NAMESPACE

    # parse usb_values dictionary
    usb_state = usb_values['usb_state']
    serial_value = usb_values['serial_value']

    # send message to server
    USB_NAMESPACE.emit('send_usb_update', {'serial_value': serial_value, 'usb_state': usb_state})


def create_socket(persistent):
    global SOCKETIO, USB_NAMESPACE

    if persistent:
        USB_NAMESPACE.on('server_pull_usb', notify_value)
        SOCKETIO.wait()

    else:
        SOCKETIO.wait(seconds=2)

def main():
    global DATA

    parser = argparse.ArgumentParser(description=__doc__,
                   formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument("--persistent", dest="persistent",
        help="number of things", action='store_true', default=False)

    args = vars(parser.parse_args())

    persistent = args['persistent']

    create_socket(persistent)
    notify_value(DATA)


if __name__ == "__main__":
    main()



