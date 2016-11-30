#!/usr/bin/env python

from socketIO_client import SocketIO, LoggingNamespace, BaseNamespace
import logging
import argparse
import subprocess
import json
import os, sys

logging.getLogger('requests').setLevel(logging.WARNING)
logging.basicConfig(level=logging.DEBUG)

class NodeNamespace(BaseNamespace):

    def on_aaa_response(self, *args):
        print('on_aaa_response', args)

SOCKETIO = SocketIO('10.31.77.36', 5000)
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

    if node_command == 'pair' or node_command == 'unpair':
        # run pair/unpair command
        pair_unpair(serial_value, node_command)
        print("RUNNING: " + node_command)

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
    datafile = open('/home/pirate/CODE/pear-sd/paired_devices.txt').read()

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

    if node_command == 'pair':
        print("I SHOULD BE PAIRING NOW")

        # add udev rule to 10-local.rules (create file if not exist)
        udev_pair(serial_value)

        # add paired usb serial to paired_devices.txt
        with open('/home/pirate/CODE/pear-sd/paired_devices.txt', 'a+') as myfile:
            myfile.write(serial_value + '\n')
            myfile.close()

            PAIRED_STATUS = 'paired'

        # initialize USB flash drive
        initialize_usb()
        print("I'M DONE PAIRING")

    elif node_command == 'unpair':
        print("I SHOULD BE UNPAIRING NOW")

        # remove udev rule from 10-local.rules
        udev_unpair(serial_value)

        # remove paired usb serial from paired_devices.txt
        with open('/home/pirate/CODE/pear-sd/paired_devices.txt', 'a+') as myfile:
            lines = myfile.readlines()

            # delete all content of file
            myfile.seek(0)
            myfile.truncate()

            # write new lines to file
            for line in lines:
                #if line != serial_value + '\n':
                if serial_value + '\n' != line:
                    myfile.write(line)
            #myfile.truncate()
            myfile.close()

            PAIRED_STATUS = 'not_paired'
            print("I'M DONE UNPARING")

    return PAIRED_STATUS

def udev_pair(serial_value):
    # udev rule file to create if doesn't exist
    udev_rule_path = '/etc/udev/rules.d/10-local.rules'

    # get current working directory
    cwd = os.getcwd()

    # temp udev rule file
    tmp = '10-local.rules'

    # udev rule to add
    rules = [
        '# pair usb flash drive: ' + serial_value + ', give it a persistent name and RUN usb_sync script upon add event (created by pear-sd)\n',
        'KERNEL=="sd*1", ' + serial_value + ', ACTION=="add", SYMLINK+="janus_usb", RUN+="' + cwd + '/scripts/usb_sync"\n'
    ]


    # create temporary file from scratch
    with open(tmp, 'a+') as temp:
        # iterate over rules list
        for rule in rules:
            # write one line at a time
            temp.write(rule)
        # close file when done writing
        temp.close()

    temp_file = open(tmp, 'rt').read()


    # check if udev rule file already exists
    if not os.path.exists(udev_rule_path):
        # if file DOES NOT exist do this

        # move tmp file to /etc/udev/rules.d
        os.system("sudo mv " + tmp + " " + udev_rule_path)

        # reset udev rules
        os.system("sudo udevadm control --reload-rules")

    # otherwise, check if file DOES exist
    elif os.path.exists(udev_rule_path):
        # if file DOES exist do this:
        # open and read existing file
        with open(udev_rule_path, 'rt') as existing_file:
            # concat existing file and new tmp file
            new_file = existing_file.read() + '\n' + temp_file
            with open(tmp, 'wt') as output:
                output.write(new_file)

        # move tmp file to /etc/udev/rules.d
        os.system("sudo mv " + tmp + " " + udev_rule_path)

        # reset udev rules
        os.system("sudo udevadm control --reload-rules")


def udev_unpair(serial_value):
    # existing udev rule file
    udev_rule_path = '/etc/udev/rules.d/10-local.rules'

    # temp udev rule file
    tmp = '10-local.rules'

    # create temporary file from scratch
    '''
    with open(tmp, 'a+') as temp:
        temp.write('\n')
        temp.close()
    '''

    # remove paired usb serial from paired_devices.txt
    # open existing udev rules file 10-local.rules
    with open(udev_rule_path, 'rt') as existing_file:
        blank_line = 0
        # read lines of 10-local.rules
        lines = existing_file.readlines()
        # open tmp udev file
        with open(tmp, 'a+') as output:
            for line in lines:
                if serial_value not in line:
                    if line == '\n' and blank_line == 0:
                        output.write(line)
                        output.truncate()
                        blank_line += 1
                    elif line != '\n':
                        output.write(line)
                        output.truncate()
                        blank_line = 0
            output.close()

        existing_file.close()

    '''
    with open(tmp, 'r+') as new_output:
        new_lines = new_output.readlines()
        print(new_lines)
        new_lines = new_lines[:-1]
        print(new_lines)
        new_output.seek(0)
        for new_line in new_lines:
            new_output.write(new_line)
            new_output.truncate()
        new_output.close()
    '''

    # move tmp file to /etc/udev/rules.d
    os.system("sudo mv " + tmp + " " + udev_rule_path)

    # reset udev rules
    os.system("sudo udevadm control --reload-rules")


def initialize_usb(*message):
    print("INITIALIZING USB")
    # emit initialize message to server
    NODE_NAMESPACE.emit('initialize_usb', {'node_message': 'INITIALIZING'})


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



