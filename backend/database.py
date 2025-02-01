#create DB tables and schema
#1 table for card ID, Card Name, Current value

import sqlite3
from datetime import datetime

# Existing Database File
DB_FILE = "pokemon.db"


def create_table():
    """Creates the pokemon_cards table if it does not exist."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pokemon_cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                value REAL NOT NULL,
                rarity TEXT,
                set_name TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
    print("Table 'pokemon_cards' has been created or already exists.")

# Run the function
if __name__ == "__main__":
    create_table()
