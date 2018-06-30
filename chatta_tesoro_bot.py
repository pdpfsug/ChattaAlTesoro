"""
Makerspace - Chatta al Tesoro
Game Bot

This project is splitted in 2 bots, one for the preparation of the game
and a second one for the actual game.

Author: Radeox (radeox@pdp.linux.it)
"""

#!/bin/python3.6
import os
import sys
import uuid
import sqlite3
import io
import datetime
import subprocess
from time import time, sleep
import telepot
import zbarlight
from PIL import Image
from settings import TOKEN_GAME, PASSWORD, DB_NAME, TOKEN_ADMIN
from random import randint
from telepot.namedtuple import ReplyKeyboardMarkup, ReplyKeyboardRemove

class State(object):

    def __init__(self, value, riddle_id='', solution='', kind=None,
                    msg_success='Esatto!', msg_error="Errore!"):
        self.state = value
        self.riddle_id = riddle_id
        self.solution = solution
        self.ban_time = 0
        self.msg_success = msg_success
        self.msg_error = msg_error
        self.kind = kind

    def __eq__(self, value):
        return self.state == value

class UserState(dict):

    def __setitem__(self, key, value):
        if isinstance(value, State):
            super().__setitem__(key, value)
        elif key not in self  and isinstance(value, int):
            super().__setitem__(key, State(value))
        else:
            self[key].state = value


# Global variables
USER_STATE = UserState()
TEMPS = {}
SLEEP_TIME = 6


def handle(msg):
    """
    This function handle all incoming messages from users
    """
    content_type, chat_type, chat_id = telepot.glance(msg)
    print("Messaggio: %s" % msg)

    # Init user state if don't exist
    if chat_id not in USER_STATE:
        next_riddle_id = get_next_riddle_id(chat_id)
        if next_riddle_id:
            riddle = get_riddle(next_riddle_id)
        else:
            USER_STATE[chat_id] = 0
            riddle = None

        if riddle:
            #USER_STATE[chat_id] = 2
            USER_STATE[chat_id] = State(
                value=2, riddle_id=next_riddle_id, solution=riddle[8],
                kind=riddle[1], msg_success=riddle[9] or "Esatto!",
                msg_error=riddle[10])
        else:
            USER_STATE[chat_id] = 0

    # Check if user is banned
    try:
        if TEMPS[chat_id]['ban_time'] > TEMPS['time']:
            bot.sendMessage(chat_id, "Riprova tra {0} secondi".format(TEMPS[chat_id]['ban_time'] - TEMPS['time']))
            return
    except KeyError:
        pass

    # Handle message
    if content_type == 'text':
        command_input = msg['text']

        if command_input == '/start':
            bot.sendMessage(chat_id, "Ciao! Se stai leggendo questo messaggio, vuol dire che sei passato davanti allo scoiattolo. Prima di continuare ascolta bene...")
            bot.sendMessage(chat_id, "https://youtu.be/wRMaGacdics")
            sleep(SLEEP_TIME)
            bot.sendMessage(chat_id, "Esatto, ho bisogno che tu e i tuoi amici mi aiutiate.\n"
                "Potete farlo! Basta formare un gruppo che va dai 2 ai 5 componenti.")
            sleep(SLEEP_TIME)
            bot.sendMessage(chat_id, "Usa il comando /iscrivimi per registrare il tuo gruppo, proseguendo con la registrazione dichiari di aver letto e accettato i termini del /regolamento")
            return

        if command_input == '/regolamento':
            bot.sendMessage(chat_id, "REGOLAMENTO\n"
                "Vorrei darvi anche delle raccomandazioni.\n\n"
                "Contenuto del regolamento:\n"
                "http://bit.ly/slsregolamento\n\n")
            return

        if command_input == '/help' or command_input == '/aiuto':
            bot.sendMessage(chat_id, "/iscrivimi - Iscrivi la tua squadra\n"
                "/tempo - Quanto manca alla fine della caccia al tesoro\n"
                "/regolamento - Regolamento di gioco\n"
                "/aiuto - Elenco dei comandi\n")
            return

        if command_input == '/id':
            bot.sendMessage(chat_id, '{}'.format(chat_id))
            return

        if command_input == '/tempo':
            if game_started():
                now = datetime.datetime.now()
                end_game = now.replace(hour=19, second=0, microsecond=0)
                delta = str(end_game - now).split('.')[0]
                bot.sendMessage(chat_id, "Il gioco terminerà alle 19:00\nRimagono: {}".format(delta))
            else:
                bot.sendMessage(chat_id, 'Il gioco non è ancora iniziato!')
            return

        # Register Team
        elif command_input == '/iscrivimi':
            if game_started():
                bot.sendMessage(chat_id, "Mi dispiace ma la caccia al tesoro è già cominciata...")
            else:
                USER_STATE[chat_id] = 1
                bot.sendMessage(chat_id, "Fantastico! Grazie 😉\n"
                    "Per poter proseguire inviatemi il nome del vostro gruppo (esempio: “Nomegruppo”).\n"
                    "Siate creativi nella scelta del nome, vi renderà unici!")
            return

        # Register Team - 2
        elif USER_STATE[chat_id] == 1:
            USER_STATE[chat_id] = 3 # invio foto gruppo

            # Leader name
            lname = ""
            try:
                lname = msg['from']['username']
                lname = msg['from']['first_name']
                lname = msg['from']['first_name'] + ' ' + msg['from']['last_name']
            except KeyError:
                pass

            if add_team(chat_id, command_input, lname):
                bot.sendMessage(chat_id, "team{} è ufficiale: siete in gioco!\nPer suggellare la nostra alleanza, inviatemi una vostra foto insieme allo scoiattolo, può essere un selfie o potete chiedere a qualcuno di farvela scattare, l’importante è che facciate una bella smorfia di gruppo.".format(command_input))
            else:
                bot.sendMessage(chat_id, "Sembra che tu sia già registrato, in caso contrario parla con qualcuno dello staff!")

        # Response to riddle
        elif USER_STATE[chat_id] == 2:
            if game_started():
                # Recover solution
                solution = TEMPS[chat_id]['solution']
                ridd_id = TEMPS[chat_id]['ridd_id']
                riddle = get_riddle(ridd_id)

                kind = riddle[1]

                if kind == 'multiple':
                    user_given_solution = command_input[0]
                elif kind == 'open':
                    user_given_solution = command_input

                if user_given_solution.upper() == solution.upper():
                    # Mark as solved
                    USER_STATE[chat_id] = State(value=0)

                    if add_solved(chat_id, ridd_id):
                        # Get next riddle position

                        # invio messaggio di successo
                        msg_success = riddle[9] or 'Esatto!'
                        send_splitted_message(bot, chat_id, msg_success)

                        data = get_next_riddle_location(chat_id)
                        if data:
                            latitude = data[0]
                            longitude = data[1]
                            help_img = data[2]

                            if help_img != '':
                                with open('img/' + help_img, 'rb') as f:
                                    bot.sendPhoto(chat_id, f, reply_markup=ReplyKeyboardRemove(remove_keyboard=True))
                            else:
                                bot.sendLocation(chat_id, latitude, longitude, reply_markup=ReplyKeyboardRemove(remove_keyboard=True))
                        else:
                            # Solved everything
                            team_end_game(chat_id)
                    else:
                        # Already solved riddle
                        bot.sendMessage(chat_id, "Sembra che abbiate già risolto questo indovinello", reply_markup=ReplyKeyboardRemove(remove_keyboard=True))
                else:
                    # Ban user for some time on wrong answer
                    TEMPS[chat_id]['ban_time'] = int(time()) + 60
                    riddle = get_riddle(ridd_id)
                    error_message = riddle[10]
                    if not error_message:
                        error_message = 'Sbagliato!'
                    send_splitted_message(bot, chat_id, error_message)
                    bot.sendMessage(chat_id, "Riprova tra 60 secondi")
            else:
                USER_STATE[chat_id] = 0
                bot.sendMessage(chat_id, "Mi dispiace ma sembra che la caccia al tesoro sia finita", reply_markup=ReplyKeyboardRemove(remove_keyboard=True))
        else:
            bot.sendMessage(chat_id, "Mi dispiace, non conosco questo comando 😦\nUsa /help")

    # foto della squadra per la registrazione
    elif content_type == 'photo' and USER_STATE[chat_id] == 3:

        team_name = get_team(chat_id)
        admin_bot = telepot.Bot(TOKEN_ADMIN)
        photo = bot.getFile(msg['photo'][-1]['file_id'])
        photo_file = io.BytesIO()
        bot.download_file(photo['file_id'], photo_file)
        photo_file.seek(0)
        for admin in get_admins():
            msg_to = admin[0]
            # Inviare tramite file_id non funziona (Bad Request: wrong file identifier/HTTP URL specified)
            # https://core.telegram.org/bots/api#sending-files
            # file_id is unique for each individual bot and can't be transferred from one bot to another
            admin_bot.sendPhoto(msg_to, photo_file, caption="Nuovo team: {}".format(team_name[0]))
        del(photo_file)

        bot.sendMessage(chat_id, "Molto bene! Condividetela sui vostri profili social con gli hashtag #seguiloscoiattolo #team{}.\nFatela girare, la foto che riceverà  più like entro le 19:00 del 29 giugno vincerà una vacanza con me! 😛".format(get_team(chat_id)[0]))
        sleep(SLEEP_TIME)
        bot.sendMessage(chat_id, "Ora più di questo non posso dirvi... il resto lo scoprirete tornando qui, a Piazza Salotto, alle 15:00 in punto. Non mi abbandonate e tenetevi pronti!")
        USER_STATE[chat_id] = State(value=0)

    # foto ma il gioco non è iniziato ancora
    elif content_type == 'photo' and is_registred(chat_id) and not game_started():
        bot.sendMessage(chat_id, "La caccia al tesoro non è ancora iniziata!\nDevi attendere l'inizio per iniziare a giocare, ti arriverà una notifica quando sarà il momento.")
        return

    # invio di una foto durante il gioco
    elif content_type == 'photo' and is_registred(chat_id) and game_started():
        photo_id_msg = msg['photo'][-1]['file_id']

        if 'forward_from' in msg:
            bot.sendMessage(chat_id, "Hey! Non puoi inoltrarmi delle foto, devi scattarle tu 😉")
            return

        # Download QR
        filename = str(uuid.uuid4())
        bot.download_file(photo_id_msg, filename)

        # Open QR
        with open(filename, 'rb') as f:
            image = Image.open(f)
            image.load()

        try:
            state = USER_STATE[chat_id]
            # invio di una foto richiesta dal gioco
            if state.kind == "photo":
                # la foto del gioco viene inviata al bot admin

                team_name = get_team(chat_id)
                admin_bot = telepot.Bot(TOKEN_ADMIN)
                photo = bot.getFile(photo_id_msg)
                photo_file = io.BytesIO()
                bot.download_file(photo['file_id'], photo_file)
                photo_file.seek(0)
                for admin in get_admins():
                    msg_to = admin[0]
                    # Inviare tramite file_id non funziona (Bad Request: wrong file identifier/HTTP URL specified)
                    # https://core.telegram.org/bots/api#sending-files
                    # file_id is unique for each individual bot and can't be transferred from one bot to another
                admin_bot.sendPhoto(msg_to, photo_file, caption="Risposta-foto del team {} [riddle: {}]".format(team_name[0], state.riddle_id))
                del(photo_file)

                # Segna il riddle come risolto
                add_solved(chat_id, state.riddle_id)

                # Invia il messaggio di successo
                send_splitted_message(bot, chat_id, state.msg_success)

                # Invia il successivo riddle
                next_riddle_id = get_next_riddle_id(chat_id)
                if next_riddle_id:
                    ridd_id = next_riddle_id
                    riddle = get_riddle(ridd_id)
                else:
                    team_end_game(chat_id)
                    return
            # invio di un QR CODE
            else:

                # Decode QR
                codes = zbarlight.scan_codes('qrcode', image)

                # Get riddle and send it
                try:
                    ridd_id = codes[0].decode()
                except TypeError:
                    bot.sendMessage(chat_id, "In questa foto non riesco a riconoscere nessun QR code, riprova mettendo a fuoco e centrando meglio il QR.")
                    return

                riddle = get_riddle(ridd_id)

                if not riddle:
                    bot.sendMessage(chat_id, 'QR non valido! Riprova')
                    return

                next_riddle = get_next_riddle_id(chat_id)

                if ridd_id != next_riddle:
                    bot.sendMessage(chat_id, "Hai inviato il QR code di una tappa sbagliata, segui l'ordine corretto delle domande!")
                    return

            if riddle:
                USER_STATE[chat_id] = State(
                    value=2, riddle_id=ridd_id, solution=riddle[8],
                    kind=riddle[1], msg_success=riddle[9] or "Esatto!",
                    msg_error=riddle[10])

                # Save answers for next message
                # TODO: replace them by using the State object, but do a careful testing!
                # TODO: (better do it after Pescara!)
                TEMPS[chat_id] = {}
                TEMPS[chat_id]['ridd_id'] = ridd_id
                TEMPS[chat_id]['solution'] = riddle[8]
                print(TEMPS)

                # Prepare answer keyboard
                markup = ReplyKeyboardMarkup(keyboard=[
                    [riddle[x]] for x in range(2,8) if riddle[x]
                ], one_time_keyboard=True)
                if riddle[1] == 'open':
                    markup = None

                bot.sendChatAction(chat_id, 'typing')
                sleep(SLEEP_TIME)

                # invio nuova domanda
                send_splitted_message(bot, chat_id, riddle[0], markup=markup)

        except Exception as e:
            raise
            bot.sendMessage(chat_id, 'QR non riconosciuto! Riprova')
        finally:
            # Remove used file
            os.unlink(filename)

    elif content_type == 'photo' and not is_registred(chat_id):
        is_game_started = game_started()
        if is_game_started:
            bot.sendMessage(chat_id, "Mi dispiace, ma il gioco è già iniziato.\nDovrai attendere la prossima caccia al tesoro!")
        else:
            bot.sendMessage(chat_id, "Non sei registrato! Usa il comando /iscrivimi")

def team_end_game(chat_id):

    sleep(SLEEP_TIME)
    if chat_id == get_winning_team_id():
        send_splitted_message(bot, chat_id, "Siete riusciti a liberare il potere! Andate allo stand dell’IRF a scoprire cosa vi attende!---http://bit.ly/2lJOuu6")
        admin_bot = telepot.Bot(TOKEN_ADMIN)
        for admin in get_admins():
            admin_bot.sendMessage(admin[0], "La squadra {} ({}) ha vinto!".format(get_team(chat_id)[0], chat_id))
    else:
        send_splitted_message(bot, chat_id, "Hai completato tutte le prove ma purtroppo sei arrivato troppo tardi 🙁---Goditi comunque la serata e grazie per aver partecipato!")

    # invio credits
    sleep(SLEEP_TIME)
    send_splitted_message(bot, chat_id, "Questa caccia al tesoro è stata realizzata dagli studenti del biennio specialistico dell’ISIA Pescara Design www.isiadesign.pe.it\ncon la preziosa collaborazione tecnica offerta da beFair https://www.befair.it/")

def get_winning_team_id():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT ridd_id FROM riddle ORDER BY sorting DESC LIMIT 1;")
    last_riddle_id = c.fetchone()[0]
    c.execute("SELECT team FROM solved_riddle WHERE riddle='{}' ORDER BY timestamp LIMIT 1;".format(last_riddle_id))
    winner = c.fetchone()
    if winner:
        winner_id = winner[0]
    else:
        winner_id = None
    conn.close()
    return winner_id

def send_splitted_message(bot, chat_id, message, markup=None):
    messages = [x.strip() for x in message.split('---')]
    last_message_with_markup = messages.pop()
    last_message_with_markup = last_message_with_markup.replace('$$$NOMESQUADRA$$$', get_team(chat_id)[0])
    for message in messages:
        message = message.replace('$$$NOMESQUADRA$$$', get_team(chat_id)[0])
        if message:
            bot.sendMessage(chat_id, message, reply_markup=ReplyKeyboardRemove(remove_keyboard=True))
        bot.sendChatAction(chat_id, 'typing')
        sleep(SLEEP_TIME)
    bot.sendMessage(chat_id, last_message_with_markup, reply_markup=markup)

# Utility functions
def game_started():
    """
    Return game state
    """
    if not os.path.isfile('tesoro.lock'):
        return 0
    else:
        return 1


# Database related functions
def add_team(chat_id, team_name, leader_name):
    """
    Add new Team to database
    """
    # Open DB
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    query = 'INSERT INTO team(chat_id, team_name, leader_name) VALUES (?, ?, ?)'

    try:
        c.execute(query, (chat_id, team_name, leader_name))
        conn.commit()
    except sqlite3.IntegrityError:
        return 0
    finally:
        # Finally close connection
        conn.close()
    return 1

def add_solved(chat_id, ridd_id):
    """
    Mark as solved the riddle for given team
    """
    # Open DB
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    try:
        query = 'INSERT INTO solved_riddle(team, riddle) VALUES({0}, "{1}")'.format(chat_id, ridd_id)
        c.execute(query)
        conn.commit()
    except sqlite3.IntegrityError:
        return 0
    finally:
        # Finally close connection
        conn.close()
    return 1

def is_registred(chat_id):
    """
    Check if user is registred as team
    """
    # Open DB
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute('SELECT COUNT(*) FROM team WHERE chat_id == {0}'.format(chat_id))
    rv = c.fetchone()[0]

    # Finally close connection
    conn.close()

    return rv

def get_riddle(ridd_id):
    """
    Get riddle from DB
    """
    # Open DB
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    query = ('SELECT question, kind, answer1, answer2, answer3, answer4, answer5, answer6, solution, msg_success, msg_error '
             'FROM riddle WHERE ridd_id == "{0}"'.format(ridd_id))
    c.execute(query)
    riddle = c.fetchone()

    # Finally close connection
    conn.close()

    return riddle

def get_next_riddle_id(chat_id):

    # Open DB
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Get number of not solved riddles
    query = ('SELECT ridd_id FROM riddle WHERE '
             'sorting = (SELECT MIN(sorting) as next_sorting_id '
             'FROM riddle '
             'WHERE ridd_id NOT IN '
             '(SELECT riddle FROM solved_riddle WHERE team = {0}))'.format(chat_id))
    c.execute(query)
    next_riddle_id = c.fetchone()
    # TODO: gestire risposta None
    if next_riddle_id:
        return next_riddle_id[0]
    else:
        return None

    conn.close()
    return next_riddle_id


def get_next_riddle_location(chat_id):
    """
    Get next riddle location from DB
    """
    # Open DB
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    next_ridd_id = get_next_riddle_id(chat_id)

    # There is still something to find
    if next_ridd_id:

        query = 'SELECT latitude, longitude, help_img FROM riddle WHERE ridd_id = ?'
        c.execute(query, (next_ridd_id,))

        data = c.fetchone()

        # Finally close connection
        conn.close()

        return data
    else:
        return 0

def get_admins():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    query = 'SELECT chat_id FROM admin'
    c.execute(query)
    data = c.fetchall()
    return data

def get_team(chat_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    query = 'SELECT team_name FROM team WHERE chat_id={}'.format(chat_id)
    c.execute(query)
    data = c.fetchone()
    return data


### Main ###
if __name__ == "__main__":
    print("Starting Makerspace - ChattaAlTesoroBot...")

    # PID file
    PID = str(os.getpid())
    PIDFILE = "/tmp/mk_cat.pid"

    # Check if PID exist
    if os.path.isfile(PIDFILE):
        try:
            subprocess.check_call(["/usr/bin/pgrep", "-F", PIDFILE])
        except subprocess.CalledProcessError:
            os.remove(PIDFILE)
        else:
            print("Process GameBot is already running (see %s), exiting!" % PIDFILE)
            sys.exit(100)

    # Create PID file
    with open(PIDFILE, 'w') as f:
        f.write(PID)
        f.close()

    # Start working
    try:
        bot = telepot.Bot(TOKEN_GAME)
        bot.message_loop(handle)

        while 1:
            TEMPS['time'] = int(time())
            sleep(1)
    finally:
        os.unlink(PIDFILE)
