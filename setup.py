#!/usr/bin/env python

import os, sys

# for both
def install_pip_packages():
    os.system("sudo pip install -r requirements.txt")

# for both, but device_type dependent
def create_directories(device_type):
    
    # folders to use if device_type != node (i.e. == client)
    folders = ['/logs/']

    # but, if device_type == node, create these folders
    if device_type != 'server':
        folders = ['/logs/', '/usb_mount/', '/credentials/']

    # get current working directory
    cwd = os.getcwd()

    for folder in folders:

        # concat full path to directory
        full_path = cwd + folder

        # create directory if doesn't exist
        if not os.path.exists(full_path):
            os.mkdir(full_path)
            # add gitkeep to directory
            file_name = '.gitkeep'
            with open(file_name, 'a+') as new_file:
                new_file.write('###')
                new_file.close()
            print('created directory: ' + full_path)


# node only
def create_paired_devices_file():

    # get current workign directory
    cwd = os.getcwd()

    # files to create
    files = ['paired_devices.txt']

    # create files if don't already exist
    for f in files:
        new_file = cwd + "/" + f
        open(new_file, 'a+')
        print('created file: ' + new_file)


# client only
def create_udev_rules():

    # udev rule file to create if doesn't exist
    udev_rule_path = '/etc/udev/rules.d/10-local.rules'

    # get current working directory
    cwd = os.getcwd()

    # temp udev rule file
    tmp = '10-local.rules'

    # udev rules
    rules = [
        '# persistent name for physical usb port 1.2 (created by pear-sd)\n',
        'KERNEL=="sd*1", ATTRS{devpath}=="1.2", SYMLINK+="external_usb"\n',
        '\n',
        '# script to run when usb/sd CONNECTED to usb 1.2 (created by pear-sd)\n',
        'KERNEL=="sd*1", ATTRS{devpath}=="1.2", ACTION=="add", RUN+="' + cwd + '/scripts/get_usb_update"\n',
        '\n',
        '# script to run when usb/sd DISCONNECTED from usb 1.2 (created by pear-sd)\n',
        'KERNEL=="sd*1", ATTRS{devpath}=="1.2", ACTION=="remove", RUN+="' + cwd + '/scripts/get_usb_update"\n'
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
            new_file = existing_file.read() + '\n\n' + temp_file + '\n'
            with open(tmp, 'wt') as output:
                output.write(new_file)

        # move tmp file to /etc/udev/rules.d
        os.system("sudo mv " + tmp + " " + udev_rule_path)

        # reset udev rules
        os.system("sudo udevadm control --reload-rules")

def remove_unused_directories(device_type):
    # remove templates and static directories for NODE and CLIENT (no web UI needed)
    if device_type != 'server':
        os.system("sudo rm -r templates static")
        print('removed directory: /templates')
        print('removed directory: /static')

def remove_unused_scripts(device_type):

    # keep only server.py
    if device_type == 'server':
        os.system("sudo rm usb_client.py node_client.py")
        os.system("sudo apt-get -y install libevent-dev python-all-dev")
        print('removed script: usb_client.py')
        print('removed script: node_client.py')

    # keep only usb_client.py
    elif device_type == 'client':
        os.system("sudo rm server.py node_client.py")
        print('removed script: server.py')
        print('removed script: node_client.py')

    # keep only node_client.py
    elif device_type == 'node':
        os.system("sudo rm usb_client.py server.py")
        print('removed script: server.py')
        print('removed script: usb_client.py')


def install_pip():
    os.system('sudo apt-get -y install python-pip')
    os.system('sudo easy_install pip')

def install_rsync():
    os.system('sudo apt-get -y install rsync')

# setup.py --server runs this
if sys.argv[-1] == '--server':
    
    device_type = 'server'

    # let user know what's going on
    print("setting up pear-sd for device type: SERVER")
    
    # run setup functions for NODE
    install_pip()
    install_pip_packages()
    create_directories(device_type)
    remove_unused_directories(device_type)
    remove_unused_scripts(device_type)

    # exit
    sys.exit()


# setup.py --node runs this
if sys.argv[-1] == '--node':

    device_type = 'node'

    # let user know what's going on
    print("setting up pear-sd for device type: NODE")
    
    # run setup functions for NODE
    install_pip()
    install_pip_packages()
    install_rsync()
    create_directories(device_type)
    create_paired_devices_file()
    remove_unused_directories(device_type)
    remove_unused_scripts(device_type)

    # exit
    sys.exit()

# setup.py --client runs this
if sys.argv[-1] == '--client':

    device_type = 'client'

    print("setting up pear-sd for device type: USB CLIENT")

    # run setup functions for CLIENT
    install_pip()
    install_pip_packages()
    install_rsync()
    create_directories(device_type)
    create_udev_rules()
    remove_unused_directories(device_type)
    remove_unused_scripts(device_type)

    # exit
    sys.exit()
