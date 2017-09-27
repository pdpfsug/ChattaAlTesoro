"""
Tresure Hunt - Telegram Bot

Author: Radeox (radeox@pdp.linux.it)
"""

#!/bin/python3.6
import os
import sys
import uuid
import gettext
import sqlite3

from time import sleep
from datetime import datetime
from settings import TOKEN, LANG

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
            bot.sendMessage(chat_id, _('start_msg'))

        elif command_input == '/registerTeam':
            user_state[chat_id] = 1
            bot.sendMessage(chat_id, _('team_name_msg'))
        
        elif user_state[chat_id] == 1:
            lname = msg['from']['first_name'] + ' ' + msg['from']['last_name']

            if add_team(chat_id, command_input, lname):
                bot.sendMessage(chat_id, _('registration_success'))
            else:
                bot.sendMessage(chat_id, _('registration_fail'))

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
            # TODO Do some shit here
            bot.sendMessage(chat_id, '{0}'.format(codes[0].decode()))

        except Exception as e:
            print(e)
            bot.sendMessage(chat_id, 'QR non riconosciuto! Riprova')

        finally:
            # Remove used file
            os.remove(filename)


def add_team(chat_id, team_name, leader_name):
    """
    Add new Team to database
    """

    # Open DB
    conn = sqlite3.connect('treasure_hunt.db')
    c = conn.cursor()

    try:
        c.execute('''INSERT INTO team VALUES({0}, '{1}', '{2}')'''.format(chat_id,
                                                                          team_name,
                                                                          leader_name))
        conn.commit()

        rv = 1
    except:
        rv = 0
    finally:
        # Finally close connection
        conn.close()

        return rv
            

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

# Variables
user_state = {}

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

# Localization
t = gettext.translation('messages', 'locales', languages=LANG)
_ = t.gettext

# Start working
try:
    bot = telepot.Bot(TOKEN)
    bot.message_loop(handle)

    while 1:
        sleep(10)
finally:
    os.unlink(pidfile)