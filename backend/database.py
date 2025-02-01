import sqlite3
import bcrypt

DB_FILE = "pokemon.db"

def setup_database():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()

        # 🔹 Create `users` table (if it doesn't exist)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')

        # 🔹 Add `username` column to `pokemon_cards` (if not already added)
        cursor.execute("PRAGMA table_info(pokemon_cards)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if "username" not in columns:
            cursor.execute("ALTER TABLE pokemon_cards ADD COLUMN username TEXT")

        conn.commit()
        print("✅ Database setup complete!")

# Run setup
setup_database()
