#!/bin/python3.6
import sqlite3

# Open DB
conn = sqlite3.connect('treasure_hunt.db')
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
             'riddle text,'
             'answer1 text,'
             'answer2 text,'
             'answer3 text,'
             'answer4 text,'
             'solution char,'
             'latitude int,'
             'longitude int,'
             'help_img text);')
    c.execute(query)

    query = ('CREATE TABLE solved_riddle('
             'team integer,'
             'riddle integer,'
             'is_solved bool,'
             'date date,'
             'foreign key(team) references team(chat_id),'
             'foreign key(riddle) references riddle(ridd_id),'
             'primary key(team, riddle));')
    c.execute(query)
    conn.commit()
except Exception as e:
    print(e)
finally:
    conn.close()
