"""
Makerspace - Chatta al Tesoro
Admin Bot

This project is splitted in 2 bots, one for the preparation of the game
and a second one for the actual game.

Author: Radeox (radeox@pdp.linux.it)
"""

#!/bin/python3.6
import os
import sys
import uuid
import sqlite3
from time import sleep
import qrcode
import telepot
from settings import TOKEN_ADMIN, DB_NAME, PASSWORD


def handle(msg):
    """
    This function handle all incoming messages from users
    """
    global CURRENT_ADMIN
    content_type, chat_type, chat_id = telepot.glance(msg)

    # Init user state if don't exist
    try:
        USER_STATE[chat_id] = USER_STATE[chat_id]
    except KeyError:
        USER_STATE[chat_id] = 0

    # Handle message
    if content_type == 'text':
        command_input = msg['text']

        # Public commands
        if chat_id != CURRENT_ADMIN:
            # Start with authentication
            if command_input == '/start':
                USER_STATE[chat_id] = 1
                bot.sendMessage(chat_id, "Ciao! Questo è il bot di configurazione di @ChattaAlTesoroBot.\n"
                                         "Inserisci la password.")
            elif command_input == PASSWORD and USER_STATE[chat_id] == 1:
                # Set admin
                CURRENT_ADMIN = chat_id
                USER_STATE[chat_id] = 0

                bot.sendMessage(chat_id, "Ora sei l'admin del gioco.\n"
                                         "Per terminare la configurazione digita /stop.")
            elif command_input != PASSWORD and USER_STATE[chat_id] == 1:
                bot.sendMessage(chat_id, "Password errata. Riprova")
            else:
                bot.sendMessage(chat_id, "Non hai i permessi per effetture questa operazione!")
        # Commands reserved to current admin
        else:
            # Close configuration
            if command_input == '/stop':
                CURRENT_ADMIN = 0
                bot.sendMessage(chat_id, "Configurazione completata!")

            # Start Treasure Hunt
            elif command_input == '/start_hunt':
                with open('tesoro.lock', 'w') as f:
                    f.write(PID)
                    f.close()
                bot.sendMessage(chat_id, "La caccia al tesoro è iniziata!")

            # Stop Treasure Hunt
            elif command_input == '/stop_hunt':
                os.unlink('tesoro.lock')
                bot.sendMessage(chat_id, "La caccia la tesoro è finita!")

            # Add new riddle
            elif command_input == '/add_riddle':
                USER_STATE[chat_id] = 2
                bot.sendMessage(chat_id, "Inserisci l'indovinello")

            # Add new riddle
            elif command_input == '/reset_game':
                reset_game()
                bot.sendMessage(chat_id, "Dati di gioco eliminati!")

            # New riddle text
            elif USER_STATE[chat_id] == 2:
                TMP_RIDDLE['text'] = command_input
                USER_STATE[chat_id] = 3
                bot.sendMessage(chat_id, "Inserisci le possibili risposte e la soluzione.\n"
                                         "Formato:\n"
                                         "A. Risposta1\n"
                                         "B. Risposta2\n"
                                         "C. Risposta3\n"
                                         "D. Risposta4\n"
                                         "C")

            # New riddle anwers
            elif USER_STATE[chat_id] == 3:
                # Split answers
                split = command_input.split('\n')
                TMP_RIDDLE['ans1'] = split[0]
                TMP_RIDDLE['ans2'] = split[1]
                TMP_RIDDLE['ans3'] = split[2]
                TMP_RIDDLE['ans4'] = split[3]
                TMP_RIDDLE['sol'] = split[4]

                USER_STATE[chat_id] = 4
                bot.sendMessage(chat_id, "Mandami la posizione prevista per il QR o un immagine d'aiuto")

            elif command_input == '/done' and USER_STATE[chat_id] == 5:
                ridd_id = str(uuid.uuid4())
                add_riddle(ridd_id,
                           TMP_RIDDLE['text'],
                           TMP_RIDDLE['ans1'],
                           TMP_RIDDLE['ans2'],
                           TMP_RIDDLE['ans3'],
                           TMP_RIDDLE['ans4'],
                           TMP_RIDDLE['sol'],
                           TMP_RIDDLE['lat'],
                           TMP_RIDDLE['long'],
                           TMP_RIDDLE['img'])

                USER_STATE[chat_id] = 0
                bot.sendMessage(chat_id, "Indovinello aggiunto con successo! Ecco il QR")

                # Return QR
                with open('QR.png', 'wb') as f:
                    img = qrcode.make(ridd_id)
                    img.save(f)

                with open('QR.png', 'rb') as f:
                    bot.sendPhoto(chat_id, f)

            elif command_input == '/cancel' and USER_STATE[chat_id] == 5:
                USER_STATE[chat_id] = 0
                bot.sendMessage(chat_id, "Operazione annullata")

    # Got riddle help image
    elif content_type == 'photo' and USER_STATE[chat_id] == 4:
        if not os.path.isdir('img'):
            os.mkdir('img')

        # Store img
        img_name = str(uuid.uuid4()) + '.png'
        bot.download_file(msg['photo'][-1]['file_id'], "img/" + img_name)
        TMP_RIDDLE['img'] = img_name
        TMP_RIDDLE['lat'] = ""
        TMP_RIDDLE['long'] = ""

        USER_STATE[chat_id] = 5
        bot.sendMessage(chat_id, "Inserisci /done per confermare o /cancel per annulare")

    # Get riddle location
    elif content_type == 'location' and USER_STATE[chat_id] == 4:
        TMP_RIDDLE['img'] = ""
        TMP_RIDDLE['lat'] = msg['location']['latitude']
        TMP_RIDDLE['long'] = msg['location']['longitude']

        USER_STATE[chat_id] = 5
        bot.sendMessage(chat_id, "Inserisci /done per confermare o /cancel per annulare")


# Database related functions
def add_riddle(id, text, answer1, answer2, answer3, answer4, solution, lat=None, long=None, img_name=None):
    """
    Add a new riddle in the database
    """
    # Open DB
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    query = ('INSERT INTO riddle(ridd_id, question, answer1, answer2, answer3, answer4, solution, latitude, longitude, help_img) '
             'VALUES("{0}", "{1}", "{2}", "{3}", "{4}", "{5}",'
             '"{6}", "{7}", "{8}", "{9}")'.format(id,
                                                  text,
                                                  answer1,
                                                  answer2,
                                                  answer3,
                                                  answer4,
                                                  solution,
                                                  lat,
                                                  long,
                                                  img_name))

    c.execute(query)
    conn.commit()

    # Finally close connection
    conn.close()
    return 1

def reset_game():
    """
    Reset old game data
    """
    # Open DB
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Delete old teams
    query = ('DELETE FROM team')
    c.execute(query)

    # Delete old riddles
    query = ('DELETE FROM riddle')
    c.execute(query)

    # Delete old solved_riddles
    query = ('DELETE FROM solved_riddle')
    c.execute(query)
    conn.commit()

    # Finally close connection
    conn.close()
    return 1


### Main ###
print("Starting Makerspace - ChattaAlTesoroAdminBot...")

# PID file
PID = str(os.getpid())
PIDFILE = "/tmp/mk_cat_admin.pid"

# Check if PID exist
if os.path.isfile(PIDFILE):
    print("%s already exists, exiting!" % PIDFILE)
    sys.exit()

# Variables
USER_STATE = {}
TMP_RIDDLE = {}
CURRENT_ADMIN = 0

# Create PID file
with open(PIDFILE, 'w') as f:
    f.write(PID)
    f.close()

# Start working
try:
    bot = telepot.Bot(TOKEN_ADMIN)
    bot.message_loop(handle)

    while 1:
        sleep(10)
finally:
    os.unlink(PIDFILE)
