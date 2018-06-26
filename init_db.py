#!/bin/python3.6
import sqlite3
from settings import DB_NAME

# Open DB
conn = sqlite3.connect(DB_NAME)
c = conn.cursor()

# Create tables
try:
    query = ('CREATE TABLE team('
             'chat_id integer primary key,'
             'team_name text,'
             'leader_name text);')
    c.execute(query)

    query = ('CREATE TABLE riddle('
             'ridd_id text primary key,'
             'kind text,'
             'question text,'
             'answer1 text,'
             'answer2 text,'
             'answer3 text,'
             'answer4 text,'
             'answer5 text,'
             'answer6 text,'
             'solution char,'
             'latitude int,'
             'longitude int,'
             'help_img text,'
             'msg_success text,'
             'msg_error text,'
             'sorting integer)');
    c.execute(query)

    query = ('CREATE TABLE solved_riddle('
             'team integer,'
             'riddle integer,'
             'foreign key(team) references team(chat_id),'
             'foreign key(riddle) references riddle(ridd_id),'
             'primary key(team, riddle));')

    query = ('CREATE TABLE admin(chat_id integer primary_key);')
    c.execute(query)
    conn.commit()
except Exception as e:
    print(e)
finally:
    conn.close()
