"""
Tresure Hunt - Telegram Bot

Author: Dawid Weglarz
"""

#!/bin/python3.6
import os
import sys

from time import sleep
from datetime import datetime

import telepot


def handle(msg):
    """
    This function handle all incoming messages from users
    """

    content_type, chat_type, chat_id = telepot.glance(msg)

    chat_id = msg['chat']['id']
    command_input = msg['text']

    if command_input == '/start':
        pass

    if command_input == '/stop':
        pass


def log_print(text):
    """
    Write to 'log_file' adding current date
    Debug purpose
    """
    try:
        log = open("log.txt", "a")
    except IOError:
        log = open("log.txt", "w")

    log.write("[{0}] {1}\n".format(datetime.now().strftime("%m-%d-%Y %H:%M"), text))

    log.close()


# Main
print("Starting TreasureHuntBot...")

# PID file
pid = str(os.getpid())
pidfile = "/tmp/TreasureHuntBot.pid"

# Check if PID exist
if os.path.isfile(pidfile):
    print("%s already exists, exiting!" % pidfile)
    sys.exit()

# Create PID file
with open(pidfile, 'w') as f:
    f.write(pid)
    f.close()

# Start working
try:
    bot = telepot.Bot(token)
    bot.message_loop(handle)

    while 1:
        sleep(10)
finally:
    os.unlink(pidfile)
