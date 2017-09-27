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
from settings import TOKEN, LANG, PASSWORD

import telepot
import zbarlight
from PIL import Image


def handle(msg):
    """
    This function handle all incoming messages from users
    """
    global PHASE
    content_type, chat_type, chat_id = telepot.glance(msg)

    if content_type == 'text':
        command_input = msg['text']

        # Start
        if command_input == '/start':
            bot.sendMessage(chat_id, _('start_msg'))

        # Register Team
        elif command_input == '/registerTeam':
            if PHASE == 0:
                USER_STATE[chat_id] = 1
                bot.sendMessage(chat_id, _('team_name_msg'))
            else:
                bot.sendMessage(chat_id, _('hunt_started'))
        
        # Start Treasure Hunt
        elif command_input == '/start_hunt':
            USER_STATE[chat_id] = 10
            bot.sendMessage(chat_id, _('insert_pswd'))

        # Start Treasure Hunt
        elif command_input == '/stop_hunt':
            USER_STATE[chat_id] = 11
            bot.sendMessage(chat_id, _('insert_pswd'))
        
        # Register Team
        elif USER_STATE[chat_id] == 1:
            lname = msg['from']['first_name'] + ' ' + msg['from']['last_name']

            if add_team(chat_id, command_input, lname):
                bot.sendMessage(chat_id, _('registration_success'))
            else:
                bot.sendMessage(chat_id, _('registration_fail'))

            USER_STATE[chat_id] = 0

        # Start Treasure Hunt
        elif USER_STATE[chat_id] == 10:
            if command_input == PASSWORD:
                bot.sendMessage(chat_id, _('hunt_start'))
                PHASE = 1

                USER_STATE[chat_id] = 0
                # TODO SEND TO ALL
            else:
                bot.sendMessage(chat_id, _('wrong_pswd'))

        # Stop Tresure Hunt
        elif USER_STATE[chat_id] == 11:
            if command_input == PASSWORD:
                bot.sendMessage(chat_id, _('hunt_stop'))
                PHASE = 0

                USER_STATE[chat_id] = 0
                # TODO SEND TO ALL
            else:
                bot.sendMessage(chat_id, _('wrong_pswd'))

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


### Main ###
print("Starting TreasureHuntBot...")

# Variables
USER_STATE = {}
PHASE = 0

# PID file
PID = str(os.getpid())
PIDFILE = "/tmp/TreasureHuntBot.pid"

# Check if PID exist
if os.path.isfile(PIDFILE):
    print("%s already exists, exiting!" % PIDFILE)
    sys.exit()

# Create PID file
with open(PIDFILE, 'w') as f:
    f.write(PID)
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
    os.unlink(PIDFILE)
