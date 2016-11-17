#!/usr/bin/env python

from socketIO_client import SocketIO, LoggingNamespace, BaseNamespace
import logging
import argparse
import subprocess
import json

logging.getLogger('requests').setLevel(logging.WARNING)
logging.basicConfig(level=logging.DEBUG)

class NodeNamespace(BaseNamespace):

    def on_aaa_response(self, *args):
        print('on_aaa_response', args)

SOCKETIO = SocketIO('localhost', 5000)
NODE_NAMESPACE = SOCKETIO.define(NodeNamespace, '/node')
DATA = {u'serial_value': u'no message', u'node_command': u'no message'}
PAIRED_STATUS = "unknown"
#SERIAL = "unknown"


def notify_paired(*message):
    global PAIRED_STATUS

    # parse message from server for serial_value
    message_string = json.dumps(message)
    message_dict = json.loads(message_string)[0]
    serial_value = message_dict["serial_value"]
    node_command = message_dict["node_command"]

    if node_command in 'pair' or 'unpair':
        # run pair/unpair command
        pair_unpair(serial_value, node_command)

        # determine new paired status
        PAIRED_STATUS = get_paired_status(serial_value)

        # send values to server
        send_socket_message(PAIRED_STATUS, serial_value)

    elif node_command in 'get_status':
        # determine new paired status
        PAIRED_STATUS = get_paired_status(serial_value)

        # send values to server
        send_socket_message(PAIRED_STATUS, serial_value)

def get_paired_status(serial_value):

    global PAIRED_STATUS

    # read paired_devices file to get serials
    datafile = open('/home/pirate/pear-sd/paired_devices.txt').read()

    # check if paired
    if serial_value in datafile and serial_value !='':
        PAIRED_STATUS = "paired"
    elif "ATTRS{serial}" in serial_value:
        PAIRED_STATUS = "not_paired"

    return PAIRED_STATUS

def pair_unpair(serial_value, node_command):

    global PAIRED_STATUS
    '''
    # parse message from server for node_command
    message_string = json.dumps(message)
    message_dict = json.loads(message_string)[0]
    node_command = message_dict["node_command"]
    serial_value = message_dict["serial_value"]
    '''

    if node_command in 'pair':
        with open('/home/pirate/pear-sd/paired_devices.txt', 'a+') as myfile:
            myfile.write(serial_value + '\n')
            myfile.close()

            PAIRED_STATUS = 'paired'

    elif node_command in 'unpair':
        print("I SHOULD BE UNPAIRING NOW")
        with open('/home/pirate/pear-sd/paired_devices.txt', 'a+') as myfile:
            lines = myfile.readlines()
            myfile.seek(0)
            for line in lines:
                if line != serial_value + '\n':
                    myfile.write(line)
            myfile.truncate()
            myfile.close()

            PAIRED_STATUS = 'not_paired'

    return PAIRED_STATUS

def send_socket_message(PAIRED_STATUS, serial_value):
    global NODE_NAMESPACE

    # send message to server
    NODE_NAMESPACE.emit('send_paired_status_update', {'serial_value': serial_value, 'paired_status': PAIRED_STATUS})

def create_socket(persistent):
    global SOCKETIO, NODE_NAMESPACE

    if persistent:
        NODE_NAMESPACE.on('server_pull_node', notify_paired)
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
    notify_paired(DATA)


if __name__ == "__main__":
    main()



