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
import io
import csv
import urllib.request
import sqlite3
from time import sleep
import qrcode
import telepot
from settings import TOKEN_ADMIN, DB_NAME, PASSWORD, TOKEN_GAME

# Variables
USER_STATE = {}
TMP_RIDDLE = {}
CURRENT_ADMIN = []


def handle(msg):
    """
    This function handle all incoming messages from users
    """
    global CURRENT_ADMIN

    CURRENT_ADMIN = []
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    query = 'SELECT chat_id FROM admin'
    c.execute(query)
    data = c.fetchall()
    conn.close()
    for admin in data:
        CURRENT_ADMIN.append(admin[0])

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
        if chat_id not in CURRENT_ADMIN:
            # Start with authentication
            if command_input == '/start':
                USER_STATE[chat_id] = 1
                bot.sendMessage(chat_id, "Ciao! Questo è il bot di configurazione di @ChattaAlTesoroBot.\n"
                                         "Inserisci la password.")
            elif command_input == PASSWORD and USER_STATE[chat_id] == 1:
                # Set admin
                USER_STATE[chat_id] = 0
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                query = 'INSERT INTO admin(chat_id) VALUES({})'.format(chat_id)
                c.execute(query)
                conn.commit()
                conn.close()
                bot.sendMessage(chat_id, "Ora sei l'admin del gioco.\n"
                                         "Per terminare la configurazione digita /stop.")
            elif command_input != PASSWORD and USER_STATE[chat_id] == 1:
                bot.sendMessage(chat_id, "Password errata. Riprova")
            else:
                bot.sendMessage(chat_id, "Non hai i permessi per effetture questa operazione!")
        # Commands reserved to current admin
        else:

            if command_input == '/squadre':
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                query = 'SELECT chat_id, team_name, leader_name FROM team'
                c.execute(query)
                data = c.fetchall()
                conn.close()
                bot.sendMessage(chat_id, 'Ecco la lista delle squadre registrate:')
                for team in data:
                    bot.sendMessage(chat_id, team[1])

            # Close configuration
            if command_input == '/stop':
                bot.sendMessage(chat_id, "Configurazione completata!")

            # Start Treasure Hunt
            elif command_input == '/start_hunt':
                with open('tesoro.lock', 'w') as f:
                    f.write(PID)
                    f.close()
                game_bot = telepot.Bot(TOKEN_GAME)
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                query = 'SELECT chat_id FROM team'
                c.execute(query)
                data = c.fetchall()
                conn.close()
                coords_first_position = [42.472441, 14.20929]
                bot.sendMessage(chat_id, "Eccovi! Sono felice che siate tornati. Siete pronti?\n"
                    "Io no... ma al bando la paura!\n"
                    "Iniziamo insieme questa avventura!")
                bot.sendMessage(chat_id, "Abbiamo a disposizione solo quattro ore, potete controllare il tempo rimanente scrivendo /tempo.\n"
                    "Il primo luogo da raggiungere non è molto lontano da voi.\n")
                bot.sendMessage(chat_id, "Vi dico solo “Se lu mar è bell lu gabbian...frect!”\n"
                    "Che l’avventura abbia inizio! In bocca allo scoiatt… ehm, al lupo! Conto su di voi.")
                bot.sendLocation(chat_id, coords_first_position[0], coords_first_position[1])
                for team in data:
                    game_bot.sendMessage(team[0], "Eccovi! Sono felice che siate tornati. Siete pronti?\n"
                        "Io no... ma al bando la paura!\n"
                        "Iniziamo insieme questa avventura!")
                    game_bot.sendMessage(team[0], "Abbiamo a disposizione solo quattro ore, potete controllare il tempo rimanente scrivendo /tempo.\n"
                        "Il primo luogo da raggiungere non è molto lontano da voi.\n")
                    game_bot.sendMessage(team[0], "Vi dico solo “Se lu mar è bell lu gabbian...frect!”\n"
                        "Che l’avventura abbia inizio! In bocca allo scoiatt… ehm, al lupo! Conto su di voi.")
                    game_bot.sendLocation(team[0], coords_first_position[0], coords_first_position[1])
                    
                bot.sendMessage(chat_id, "(notifica inviata ai giocatori)")

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

                USER_STATE[chat_id] = 40
                
                bot.sendMessage(chat_id, "Cosa devo dire al giocatore quando risponde correttamente?")
            
            elif USER_STATE[chat_id] == 40:
                TMP_RIDDLE['msg_success'] = command_input
                
                USER_STATE[chat_id] = 41
                bot.sendMessage(chat_id, "Cosa devo dire al giocatore quando sbaglia?")
                
            elif USER_STATE[chat_id] == 41:
                TMP_RIDDLE['msg_error'] = command_input
                USER_STATE[chat_id] = 4
                bot.sendMessage(chat_id, "Mandami la posizione prevista per il QR o un immagine d'aiuto")

            elif command_input == '/done' and USER_STATE[chat_id] == 5:
                ridd_id = str(uuid.uuid4())
                add_riddle(ridd_id,
                           # TODO: aggiungere nuovo parametro KIND
                           TMP_RIDDLE['text'],
                           TMP_RIDDLE['ans1'],
                           TMP_RIDDLE['ans2'],
                           TMP_RIDDLE['ans3'],
                           TMP_RIDDLE['ans4'],
                           TMP_RIDDLE['sol'],
                           TMP_RIDDLE['lat'],
                           TMP_RIDDLE['lon'],
                           TMP_RIDDLE['img'],
                           msg_success=TMP_RIDDLE['msg_success'],
                           msg_error=TMP_RIDDLE['msg_error']
                           )

                USER_STATE[chat_id] = 0
                bot.sendMessage(chat_id, "Indovinello '%(text)s' aggiunto con successo! Ecco il QR" % TMP_RIDDLE)
                # Send QR
                with open('img/qr-%s.png' % ridd_id, 'rb') as f:
                    bot.sendPhoto(chat_id, f)

            elif command_input == '/cancel' and USER_STATE[chat_id] == 5:
                USER_STATE[chat_id] = 0
                bot.sendMessage(chat_id, "Operazione annullata")
            elif command_input == '/import' and USER_STATE[chat_id] == 0:
                USER_STATE[chat_id] = 10  # ready to get import file
                bot.sendMessage(chat_id, "Questa importazione resetterà il gioco e importerà tutti i quiz.\nAllega il file da cui importare la vita, l'Universo e tutto quanto")
            elif command_input == '/export' and USER_STATE[chat_id] == 0:
                do_csv_export(chat_id)
                bot.sendMessage(chat_id, "Hai scaricato il file della configurazione della chat")

    # Got riddle help image
    elif content_type == 'photo' and USER_STATE[chat_id] == 4:

        # Store img
        img_name = str(uuid.uuid4()) + '.png'
        bot.download_file(msg['photo'][-1]['file_id'], "img/" + img_name)
        TMP_RIDDLE['img'] = img_name
        TMP_RIDDLE['lat'] = ""
        TMP_RIDDLE['lon'] = ""

        USER_STATE[chat_id] = 5
        bot.sendMessage(chat_id, "Inserisci /done per confermare o /cancel per annulare")

    # Get riddle location
    elif content_type == 'location' and USER_STATE[chat_id] == 4:
        TMP_RIDDLE['img'] = ""
        TMP_RIDDLE['lat'] = msg['location']['latitude']
        TMP_RIDDLE['lon'] = msg['location']['longitude']

        USER_STATE[chat_id] = 5
        bot.sendMessage(chat_id, "Inserisci /done per confermare o /cancel per annulare")

    elif content_type == 'document' and USER_STATE[chat_id] == 10:
        reset_game(reset_team=False)
        with open('t.csv', 'wb') as csvfile:
            bot.download_file(msg['document']['file_id'], csvfile)
        with open('t.csv', 'r', encoding='utf-8') as csvfile:
            do_csv_import(csvfile, chat_id)

        bot.sendMessage(chat_id, "Importazione quiz terminata correttamente!")
        
        USER_STATE[chat_id] = 0

# Database related functions
def add_riddle(ridd_id, kind, text, answer1, answer2, answer3, answer4, answer5, answer6, solution, lat=None, lon=None, img_name=None, msg_success='', msg_error='', sorting=None):
    """
    Add a new riddle in the database
    """
    # Open DB
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    query = ('INSERT INTO riddle(ridd_id, kind, question, answer1, answer2, answer3, answer4, answer5, answer6, '
                'solution, latitude, longitude, help_img, msg_success, msg_error, sorting) '
                'VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)')
    
    c.execute(query, (ridd_id, kind, text, answer1, answer2, answer3, answer4, answer5, answer6,
                                    solution, lat, lon, img_name, msg_success, msg_error, sorting))
    conn.commit()

    # At the end close connection
    conn.close()

    # Create the QR code with a well-known name related to riddle
    if not os.path.isfile('img/qr-%s.png' % ridd_id):
        with open('img/qr-%s.png' % ridd_id, 'wb') as f:
            img = qrcode.make(ridd_id)
            img.save(f)


    return 1

def reset_game(reset_team=True):
    """
    Reset old game data
    """
    # Open DB
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Delete old teams
    if reset_team:
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


def do_csv_export(chat_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM riddle ORDER BY sorting ASC")
    with io.StringIO() as csvfile:
        writer = csv.writer(csvfile, quoting=csv.QUOTE_NONNUMERIC)
        result = c.fetchall()
        print(repr(result))
        writer.writerows(result)
        csvfile.seek(0)
        bot.sendDocument(chat_id, ('chatta_al_tesoro.csv', csvfile))
    c.close()
    conn.close()
    return csvfile

def do_csv_import(csvfile, chat_id):
    """
    """
    csvfile.seek(0)
    reader = csv.reader(csvfile, delimiter=',') #, quoting=csv.QUOTE_NONNUMERIC)
    for i, row in enumerate(reader):
        if not i: 
            # skip the header row
            continue
        
        (ridd_id, kind, text, answer1, answer2, answer3, answer4, answer5, answer6, 
            solution, lat, lon, img_name, msg_success, msg_error, sorting) = row

        # Create the new riddle, keep values if found,
        # create otherwise
        ridd_id = ridd_id or str(uuid.uuid4())
        if img_name.startswith('https://') or img_name.startswith('http://'):
            # Image is a link so download and save it to the img/ folder
            img_url = img_name
            # TODO: assume that the URL ends with the image extension
            ext = img_name[img_name.rfind('.'):]
            img_name = str(uuid.uuid4()) + ext
            urllib.request.urlretrieve(img_url, 'img/%s' % img_name)

        add_riddle(ridd_id, kind, text, answer1, answer2, answer3, answer4, answer5, answer6,
            solution, lat, lon, img_name, msg_success, msg_error, sorting)
        
        bot.sendMessage(chat_id, "Ecco il QR per l'indovinello %s: '%s'" % (
            sorting, ridd_id))
        # Send QR
        with open('img/qr-%s.png' % ridd_id, 'rb') as f:
            bot.sendPhoto(chat_id, f)


### Main ###
if __name__ == "__main__":

    print("Starting Makerspace - ChattaAlTesoroAdminBot...")

    # PID file
    PID = str(os.getpid())
    PIDFILE = "/tmp/mk_cat_admin.pid"

    # Check if PID exist
    if os.path.isfile(PIDFILE):
        print("%s already exists, exiting!" % PIDFILE)
        sys.exit()

    # Create PID file
    with open(PIDFILE, 'w') as f:
        f.write(PID)
        f.close()

    if not os.path.isdir('img'):
        os.mkdir('img')

    # Start working
    try:
        bot = telepot.Bot(TOKEN_ADMIN)
        bot.message_loop(handle)

        while 1:
            sleep(10)
    finally:
        os.unlink(PIDFILE)


