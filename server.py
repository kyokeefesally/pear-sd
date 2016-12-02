#!/usr/bin/env python

'''
A Flask-SocketIO server to pair usb drives with Janus nodes
'''

# Import required packages
from flask_socketio import SocketIO, emit
from flask import Flask, render_template, url_for, copy_current_request_context, session, request

import socket
import fcntl
import struct

import RPi.GPIO as GPIO
from RPLCD import CharLCD, BacklightMode

import os

# remove GPIO warnings for LCD screen
#GPIO.setwarnings(False)

# Start with a basic flask app
app = Flask(__name__)

# Flask configs
app.config['SECRET_KEY'] = 'secret!'
app.config['DEBUG'] = True

# Extra files to monitor for reloader
extra_files = ['static/js/app.js', 'templates/index.html',]

#turn the flask app into a socketio app
socketio = SocketIO(app, debug=True)

# Global variables
USB_STATE = "unknown"
SERIAL = "unknown"
PAIRED_STATUS = "unknown"

# Flask app route
@app.route('/')
def index():

    #only by sending this page first will the client be connected to the socketio instance
    return render_template('index.html')


#####################################################################
#  Events when server comes online (no namespace)
#####################################################################
@socketio.on('connect')
def server_connect():
    #print("SERVER CONNECTED")
    write_to_lcd('eth0')

#####################################################################
#  Events when web clients connect to server (namespace='/web')
#####################################################################
@socketio.on('connect', namespace='/web')
def web_connect():
    global USB_STATE, SERIAL, PAIRED_STATUS

    print('Web Client Connected')
    print("{usb_state: '" + USB_STATE + "', paired_status: '" + PAIRED_STATUS + "', serial_value: '" + SERIAL + "'}")

    if (USB_STATE or SERIAL or PAIRED_STATUS) in "unknown": 

        # pull usb client for usb value and paired status
        emit('server_pull_usb', broadcast=True, namespace='/usb')
        #emit('update_lcd', {'serial_value': SERIAL}, broadcast=True, namespace='/usb') 
        #emit('update_lcd', broadcast=True, namespace='/usb')

    else:
        emit('notify_web_clients', {'serial_value': SERIAL, 'paired_status': PAIRED_STATUS, 'usb_state': USB_STATE}, broadcast=True, namespace='/web')
        #emit('update_lcd', {'serial_value': SERIAL}, broadcast=True, namespace='/usb') 
        #emit('update_lcd', broadcast=True, namespace='/usb')


#####################################################################
#  Events when usb clients connect to server (namespace='/usb')
#####################################################################
@socketio.on('connect', namespace='/usb')
def usb_connect():
    global USB_STATE, SERIAL, PAIRED_STATUS

    print('USB Client Connected')
    print("{usb_state: '" + USB_STATE + "', paired_status: '" + PAIRED_STATUS + "', serial_value: '" + SERIAL + "'}")

    if (USB_STATE or SERIAL or PAIRED_STATUS) in "unknown": 

        # pull usb client for usb value and paired status
        emit('server_pull_usb', broadcast=True, namespace='/usb')

        node_command = 'get_status'
        emit('server_pull_node', {'node_command': node_command, 'serial_value': SERIAL}, broadcast=True, namespace='/node')
        emit('update_lcd', {'serial_value': SERIAL}, broadcast=True, namespace='/usb') 
        #emit('update_lcd', broadcast=True, namespace='/usb')

    else:
        emit('notify_web_clients', {'serial_value': SERIAL, 'paired_status': PAIRED_STATUS, 'usb_state': USB_STATE}, broadcast=True, namespace='/web')
        emit('update_lcd', {'serial_value': SERIAL}, broadcast=True, namespace='/usb') 
        #emit('update_lcd', broadcast=True, namespace='/usb')


#####################################################################
#  Events when node clients connect to server (namespace='/node')
#####################################################################
@socketio.on('connect', namespace='/node')
def node_connect():
    global USB_STATE, SERIAL, PAIRED_STATUS

    print('Node Client Connected')
    print("{usb_state: '" + USB_STATE + "', paired_status: '" + PAIRED_STATUS + "', serial_value: '" + SERIAL + "'}")

    if (USB_STATE or SERIAL or PAIRED_STATUS) in "unknown": 

        # pull usb client for usb value and paired status
        emit('server_pull_usb', broadcast=True, namespace='/usb')

    else:
        emit('notify_web_clients', {'serial_value': SERIAL, 'paired_status': PAIRED_STATUS, 'usb_state': USB_STATE}, broadcast=True, namespace='/web') 



#####################################################################
#  Receive paired_status, serial_value and usb_state from USB Client
#  & send to web clients
#####################################################################
@socketio.on('send_usb_update', namespace='/usb')
def usb_update(message):
    global PAIRED_STATUS, SERIAL, USB_STATE

    # get serial and usb_state from usb client message
    SERIAL = message['serial_value']
    USB_STATE = message['usb_state']

    # read paired_devices file to get serials
    #datafile = open('/home/pirate/pear-sd/paired_devices.txt').read()

    # Check if paired
    # if usb is connected, check if paired
    if USB_STATE in 'connected':
        # send serial_value and get_status command to node
        node_command = 'get_status'
        emit('server_pull_node', {'node_command': node_command, 'serial_value': SERIAL}, broadcast=True, namespace='/node')
        emit('update_lcd', {'serial_value': SERIAL}, broadcast=True, namespace='/usb') 
        #emit('update_lcd', broadcast=True, namespace='/usb')

    # if usb is disconnected, don't need to check paired_status with Node, can just send info to web clients
    elif USB_STATE in 'no_device':
        PAIRED_STATUS = "no_device"
        SERIAL = "no_device"
        # Send info to web clients
        emit('notify_web_clients', {'serial_value': SERIAL, 'paired_status': PAIRED_STATUS, 'usb_state': USB_STATE}, broadcast=True, namespace='/web')
        emit('update_lcd', {'serial_value': SERIAL}, broadcast=True, namespace='/usb') 
        #emit('update_lcd', broadcast=True, namespace='/usb')




#####################################################################
#  Receive pull request from web
#####################################################################
@socketio.on('web_pull_usb', namespace='/web')
def web_pull(message):

    global PAIRED_STATUS, SERIAL
    # pull usb client for usb value and paired status
    emit('server_pull_usb', broadcast=True, namespace='/usb')


#####################################################################
#  Receive pair/unpair commands from web
#####################################################################
@socketio.on('pairing_button', namespace='/web')
def pair_unpair(message):
    global PAIRED_STATUS, SERIAL, USB_STATE

    # get button_status & serial_value from web message
    node_command = message['button_status']
    SERIAL = message['serial_value']

    # send pairing command to node
    emit('server_pull_node', {'node_command': node_command, 'serial_value': SERIAL}, broadcast=True, namespace='/node')


#####################################################################
#  Receive paired_status and serial_value from Node Client
#  & send to web clients
#####################################################################
@socketio.on('send_paired_status_update', namespace='/node')
def paired_update(message):
    global PAIRED_STATUS, SERIAL, USB_STATE

    # get serial and usb_state from usb client message
    SERIAL = message['serial_value']
    PAIRED_STATUS = message['paired_status']

    # Send info to web clients
    emit('notify_web_clients', {'serial_value': SERIAL, 'paired_status': PAIRED_STATUS, 'usb_state': USB_STATE}, broadcast=True, namespace='/web')


#####################################################################
#  Initialize USB
#####################################################################
@socketio.on('initialize_usb', namespace='/node')
def initialize_usb(message):

    # pull usb client for usb value and paired status
    emit('initialize_usb', {'server_message': 'INITIALIZING'}, broadcast=True, namespace='/usb')


@socketio.on('client_pull_usb_values', namespace='/web')
def web_pull(message):

    emit('server_pull_usb', broadcast=True, namespace='/usb')


@socketio.on('disconnect', namespace='/web')
def web_disconnect():
    print('Web Client Disconnected')


@socketio.on('disconnect', namespace='/usb')
def web_disconnect():
    print('USB Client Disconnected')


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

def write_to_lcd(ifname):

    lcd = CharLCD()

    lcd.clear()
    lcd.home()
    lcd.write_string(get_hostname())
    lcd.cursor_pos = (1, 0)
    lcd.write_string(get_device_type())
    lcd.cursor_pos = (2, 0)
    lcd.write_string(get_ip_address(ifname))
    #print("LCD SHOULD BE UPDATED")

if __name__ == '__main__':
    #write_to_lcd('eth0')
    socketio.run(app, host='0.0.0.0', use_reloader=True, debug=True, extra_files=['static/js/app.js', 'templates/index.html',], port=5000)


