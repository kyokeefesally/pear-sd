#!/usr/bin/env python

from socketIO_client import SocketIO, LoggingNamespace, BaseNamespace
import logging
import argparse
import subprocess
import os, sys
import json

import RPi.GPIO as GPIO
from RPLCD import CharLCD, BacklightMode
import time
from threading import Thread, Event
from multiprocessing import Process

import socket
import fcntl
import struct

logging.getLogger('requests').setLevel(logging.WARNING)
logging.basicConfig(level=logging.DEBUG)

class UsbNamespace(BaseNamespace):

    def on_aaa_response(self, *args):
        print('on_aaa_response', args)

SOCKETIO = SocketIO('pear-sd-04.local', 5000)
USB_NAMESPACE = SOCKETIO.define(UsbNamespace, '/usb')
DATA = {u'server_message': u'no message'}
USB_STATE = "unknown"
SERIAL = "undetermined"


# update server with serial and 
def notify_value(*message):
    print("CLIENT SHOULD BE NOTIFYING VALUEeeee")
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

def initialize_usb(*message):
    # get current working directory
    cwd = os.getcwd()

    # usb mount directory
    mount_directory = cwd + '/usb_mount'

    # usb credentials directory
    credentials_directory = mount_directory + '/credentials'

    # mount USB
    os.system('sudo mount /dev/external_usb ' + mount_directory)

    # check if /credentials exists
    if not os.path.exists(credentials_directory):
        # if /credentials directory DOES NOT exist do this:
        # make credentials directory
        os.mkdir(credentials_directory)

    # unmount USB
    os.system('sudo umount ' + mount_directory)


def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    raw_ip = socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])

    pretty_ip = 'ip: ' + raw_ip

    return pretty_ip


def get_hostname():
    raw_hostname = socket.gethostname()
    pretty_hostname = 'host: ' + raw_hostname
    return pretty_hostname


def get_device_type():
    path = os.getcwd()
    #path = cwd + '/pear-sd'
    files = os.listdir(path)
    if 'usb_client.py' in files:
        device_type = 'usb_client'
    elif 'node_client.py' in files:
        device_type = 'node'
    elif 'server.py' in files:
        device_type = 'server'
    else:
        device_type = 'unknown'
    device_type = 'type: ' + device_type
    return device_type


framebuffer = [
    get_hostname(),
    get_device_type(),
    get_ip_address('eth0'),
    '',
]



lcd = CharLCD()

process = Process()
thread_stop_event = Event()



def write_to_lcd(lcd, framebuffer, num_cols):
    lcd.home()
    #lcd.clear()
    for row in framebuffer:
            lcd.write_string(row.ljust(num_cols)[:num_cols])
            lcd.write_string('\r')


def loop_string(string, lcd, framebuffer, row, num_cols, delay=0.5):
    padding = ' ' * num_cols
    s = padding + string + padding
    for i in range(len(s) - num_cols + 1):
        framebuffer[row] = s[i:i+num_cols]
        write_to_lcd(lcd, framebuffer, num_cols)
        time.sleep(delay)




'''
stop_process = 0

def start_process(s):
    global process
    process = SerialScroll()
    if s == 'stop':
        process.terminate()
'''

def manage_process(*message):

    message_string = json.dumps(message)
    message_dict = json.loads(message_string)[0]
    lcd_serial = message_dict["serial_value"]

    #print("THIS IS THE SERIA: VALUE: " + lcd_serial)

    class SerialScroll(Process):

        print("SerialScroll Process Starting")

        def __init__(self, interval=1):

            self.interval = interval
            super(SerialScroll, self).__init__()

            #process = threading.Process(target=self.run, args=())
            #process.daemon = True                            # Daemonize process
            #process.start()                                  # Start the execution


        def lcd_scroll(self):

            string = 'sn: ' + lcd_serial

            """ Method that runs forever """
            while True:
                loop_string(string, lcd, framebuffer, 3, 20)

                time.sleep(self.interval)

        def run(self):
            self.lcd_scroll()

    global process
    #process = SerialScroll()

    #print("SHOULD BE RESTARTING THREAD")

    if process.is_alive() != True:
        print("no process alive - starting process")  
        process = SerialScroll()
        process.daemon = True 
        process.start()
        #print(process.pid)
        print(process.name)
        #print("process should be aliveeeee")

    elif process.is_alive() == True:
        print(process.name)
        print("process already alive - stoppingggg")
        process.terminate()
        lcd.clear()
        #print("process is stopped - restarting")
        process = SerialScroll()
        process.daemon = True
        process.start()
        #print("process restarted")
        print(process.name)

    #if process.is_alive():
        #print("process ALIIIIVEeee")



def create_socket(persistent):
    global SOCKETIO, USB_NAMESPACE, DATA

    if persistent:
        USB_NAMESPACE.on('server_pull_usb', notify_value)
        USB_NAMESPACE.on('initialize_usb', initialize_usb)
        USB_NAMESPACE.on('update_lcd', manage_process)
        notify_value(DATA)
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



