#!/bin/python3.6
import sqlite3

# Open DB
conn = sqlite3.connect('treasure_hunt.db')
c = conn.cursor()

# Create tables
c.execute('''CREATE TABLE team(
                chat_id INTEGER PRIMARY KEY,
                team_name TEXT,
                leader_name TEXT
            );''')

c.execute('''CREATE TABLE riddle(
                ridd_id INTEGER PRIMARY KEY,
                solution TEXT,
                location TEXT
            );''')

c.execute('''CREATE TABLE team_riddle(
                chat_id INTEGER,
                ridd_id INTEGER,
                is_solved BOOL,
                date DATE,
                PRIMARY KEY(chat_id, ridd_id)
            );''')

conn.commit()

conn.close()
