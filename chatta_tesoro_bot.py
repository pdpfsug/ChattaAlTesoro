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
from time import time, sleep
import telepot
import zbarlight
from PIL import Image
from settings import TOKEN_GAME, PASSWORD, DB_NAME
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
            bot.sendMessage(chat_id, "Benvenuto in @ChattaAlTesoroBot!\n"
                                     "Usa il comando /register_team per registrare la tua squadra")

        # Register Team
        elif command_input == '/register_team':
            if game_started():
                bot.sendMessage(chat_id, "Mi dispiace ma la caccia al tesoro è già cominciata...")
            else:
                USER_STATE[chat_id] = 1
                bot.sendMessage(chat_id, "Perfetto! Inserisci il nome della tua squadra")

        # Register Team - 2
        elif USER_STATE[chat_id] == 1:
            USER_STATE[chat_id] = State(value=0)

            # Leader name
            lname = ""
            try:
                lname = msg['from']['username']
                lname = msg['from']['first_name']
                lname = msg['from']['first_name'] + ' ' + msg['from']['last_name']
            except KeyError:
                pass

            if add_team(chat_id, command_input, lname):
                bot.sendMessage(chat_id, "Registrazione avvenuta con successo!")
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
                        data = get_next_riddle_location(chat_id)

                        if data:
                            latitude = data[0]
                            longitude = data[1]
                            help_img = data[2]

                            msg_success = riddle[9] or 'Esatto!'
                            messages = [x.strip() for x in msg_success.split('---')]
                            for message in messages:
                                bot.sendMessage(chat_id, message, reply_markup=ReplyKeyboardRemove(remove_keyboard=True))
                                sleep(1.5)

                            if help_img != '':
                                with open('img/' + help_img, 'rb') as f:
                                    bot.sendPhoto(chat_id, f, reply_markup=ReplyKeyboardRemove(remove_keyboard=True))
                            else:
                                bot.sendLocation(chat_id, latitude, longitude, reply_markup=ReplyKeyboardRemove(remove_keyboard=True))
                        else:
                            # Solved everything
                            bot.sendMessage(chat_id, "Sembra che tu abbia risolto tutti gli indovinelli! Torna al punto d'incontro!", reply_markup=ReplyKeyboardRemove(remove_keyboard=True))
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
                    bot.sendMessage(chat_id, error_message)
                    bot.sendMessage(chat_id, "Riprova tra 60 secondi")
            else:
                USER_STATE[chat_id] = 0
                bot.sendMessage(chat_id, "Mi dispiace ma sembra che la caccia al tesoro sia finita", reply_markup=ReplyKeyboardRemove(remove_keyboard=True))

    elif content_type == 'photo' and is_registred(chat_id) and game_started():
        msg = msg['photo'][-1]['file_id']

        # Download QR
        filename = str(uuid.uuid4())
        bot.download_file(msg, filename)

        # Open QR
        with open(filename, 'rb') as f:
            image = Image.open(f)
            image.load()

        try: 
            state = USER_STATE[chat_id]
            if state.kind == "photo":
                # TODO: inviare la foto su un feed facebook

                # Segna il riddle come risolto
                add_solved(chat_id, state.riddle_id)

                # Invia il messaggio di successo
                bot.sendMessage(chat_id, state.msg_success)

                # Invia il successivo riddle
                next_riddle_id = get_next_riddle_id(chat_id)
                if next_riddle_id:
                    ridd_id = next_riddle_id
                else:
                    ridd_id = "pippo"
            else:    
                # Decode QR
                codes = zbarlight.scan_codes('qrcode', image)

                # Get riddle and send it 
                ridd_id = codes[0].decode()

            riddle = get_riddle(ridd_id)

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
                ])
                if riddle[1] == 'open':
                    markup = None

                # Multimessagges support: issue #11
                # Each Messagge has the "---" separator if it is a multimessage
                question = riddle[0]
                messages = [x.strip() for x in question.split('---')]
                for message in messages:
                    bot.sendMessage(chat_id, message, reply_markup=markup)
                    sleep(1.5)
            else:
                bot.sendMessage(chat_id, 'QR non valido! Riprova')
        except Exception as e:
            raise
            bot.sendMessage(chat_id, 'QR non riconosciuto! Riprova')
        finally:
            # Remove used file
            os.unlink(filename)


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
    next_riddle_id = c.fetchone()[0]
    
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


### Main ###
if __name__ == "__main__":
    print("Starting Makerspace - ChattaAlTesoroBot...")

    # PID file
    PID = str(os.getpid())
    PIDFILE = "/tmp/mk_cat.pid"

    # Check if PID exist
    if os.path.isfile(PIDFILE):
        print("%s already exists, exiting!" % PIDFILE)
        sys.exit()

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
