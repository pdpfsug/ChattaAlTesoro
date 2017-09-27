"""
Tresure Hunt - Telegram Bot

Author: Radeox (radeox@pdp.linux.it)
"""

#!/bin/python3.6
import os
import sys
import uuid

from time import sleep
from datetime import datetime
from settings import token

import telepot
import zbarlight
from PIL import Image


def handle(msg):
    """
    This function handle all incoming messages from users
    """

    content_type, chat_type, chat_id = telepot.glance(msg)
    chat_id = msg['chat']['id']

    if content_type == 'text':
        command_input = msg['text']

        if command_input == '/start':
            pass

        if command_input == '/stop':
            pass

    elif content_type == 'photo':
        msg = msg['photo'][-1]['file_id']

        # Download QR
        filename = str(uuid.uuid4())
        bot.download_file(msg, filename)

        # Open QR
        f = open(filename, 'rb')
        image = Image.open(f)
        image.load()

        try: 
            # Decode QR
            codes = zbarlight.scan_codes('qrcode', image)
            bot.sendMessage(chat_id, '{0}'.format(codes[0].decode()))

        except Exception as e:
            print(e)
            bot.sendMessage(chat_id, 'QR non riconosciuto! Riprova')

        finally:
            # Remove used file
            os.remove(filename)


def log_print(text):
    """
    Logging functon with date/time
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