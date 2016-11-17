#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from setuptools import setup, find_packages
import os, sys

'''
install_reqs = parse_requirements(os.getcwd())
print(install_reqs)
reqs = [str(ir.req) for ir in install_reqs]
'''

'''
name='pear-sd',
description='USB pairing service for Janus nodes',
author='Kyle O\'Keefe-Sally',
author_email='kyle@wework.com',
url='https://github.com/kyokeefesally/pear-sd',
packages=find_packages(exclude=('tests', 'docs'))
'''

setup(

    install_requires=[
        'Flask >= 0.11.1',
        'Flask_SocketIO >= 2.7.2',
        'socketIO_client >= 0.7.0',
        'argparse >= 1.2.1'
    ]

)


def create_directories():

    # get current working directory
    cwd = os.getcwd()

    folders = ['/logs/', '/usb_mount/', '/credentials/']

    for folder in folders:

        # concat full path to directory
        full_path = cwd + folder

        # create directory if doesn't exist
        if not os.path.exists(full_path):
            os.mkdir(full_path)
            print('created directory: ' + full_path)


def create_paired_devices_file():

    # get current workign directory
    cwd = os.getcwd()

    # files to create
    files = ['paired_devices.txt', 'kyle.txt']

    # create files if don't already exist
    for f in files:
        new_file = cwd + "/" + f
        open(new_file, 'a+')
        print('created file: ' + new_file)



if sys.argv[-1] == 'node':
    print("node")
    os.sys("sudo python setup.py install")
    sys.exit()


if sys.argv[-1] == 'kyle':
    print("kyle")
    os.sys("sudo python setup.py install")
    sys.exit()

'''
if sys.argv[-1] == 'install':
    print("install subscript")
    #os.sys("python setup.py install")
    sys.exit()
'''