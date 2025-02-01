import sqlite3

DB_FILE = "pokemon.db"

def add_value_column():
    """Adds the 'value' column to the database if it doesn't exist."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()

        # Check if 'value' column exists
        cursor.execute("PRAGMA table_info(pokemon_cards)")
        columns = [column[1] for column in cursor.fetchall()]

        if "value" not in columns:
            cursor.execute("ALTER TABLE pokemon_cards ADD COLUMN value REAL DEFAULT 0.0")
            conn.commit()
            print("✅ 'value' column added successfully!")
        else:
            print("ℹ 'value' column already exists. No changes made.")

if __name__ == "__main__":
    add_value_column()
