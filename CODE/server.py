#!/usr/bin/env python

'''
A Flask-SocketIO server to pair usb drives with Janus nodes
'''

# Import required packages
from flask_socketio import SocketIO, emit
from flask import Flask, render_template, url_for, copy_current_request_context, session, request
from random import random
from time import sleep
from threading import Thread, Event
import subprocess
from livereload import Server, shell
import os.path

# Start with a basic flask app
app = Flask(__name__)

# Flask configs
app.config['SECRET_KEY'] = 'secret!'
app.config['DEBUG'] = True

# Extra files to monitor for reloader
extra_files = ['static/js/application.js', 'templates/index.html',]

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
    return render_template('index_v2.html')


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

    else:
        emit('notify_web_clients', {'serial_value': SERIAL, 'paired_status': PAIRED_STATUS, 'usb_state': USB_STATE}, broadcast=True, namespace='/web') 


#####################################################################
#  Events when usb clients connect to server (namespace='/web')
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
    #datafile = open('/home/pirate/paired_devices.txt').read()

    # Check if paired
    # if usb is connected, check if paired
    if USB_STATE in 'connected':
        # send serial_value and get_status command to node
        node_command = 'get_status'
        emit('server_pull_node', {'node_command': node_command, 'serial_value': SERIAL}, broadcast=True, namespace='/node')

    # if usb is disconnected, don't need to check paired_status with Node, can just send info to web clients
    elif USB_STATE in 'no_device':
        PAIRED_STATUS = "no_device"
        SERIAL = "no_device"
        # Send info to web clients
        emit('notify_web_clients', {'serial_value': SERIAL, 'paired_status': PAIRED_STATUS, 'usb_state': USB_STATE}, broadcast=True, namespace='/web')




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


@socketio.on('client_pull_usb_values', namespace='/web')
def web_pull(message):

    emit('server_pull_usb', broadcast=True, namespace='/usb')


@socketio.on('disconnect', namespace='/web')
def web_disconnect():
    print('Web Client Disconnected')


@socketio.on('disconnect', namespace='/usb')
def web_disconnect():
    print('USB Client Disconnected')


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', use_reloader=True, debug=True, extra_files=['static/js/application.js', 'templates/index.html',], port=5000)


