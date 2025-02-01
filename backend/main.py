import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from pokemon_api import search_pokemon_cards, get_all_sets

# Database file
DB_FILE = "pokemon.db"

# Function to create table (if not exists)
def create_table():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pokemon_cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                value REAL DEFAULT 0.0,
                rarity TEXT,
                set_name TEXT,
                card_number TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

# Function to search for a Pokémon card using the API
def search_card():
    search_query = search_entry.get().strip()
    selected_set = set_var.get()

    if not search_query:
        messagebox.showwarning("Input Error", "Please enter a Pokémon name.")
        return

    # Clear previous search results
    listbox.delete(0, tk.END)

    # Fetch matching cards from API with set filter
    results = search_pokemon_cards(search_query, selected_set)

    if not results:
        messagebox.showinfo("No Results", f"No cards found for '{search_query}' in '{selected_set}'.")
        return

    # Populate Listbox with results
    for card in results:
        display_text = f"{card['name']} - {card['set_name']} (#{card['card_number']}) - {card['rarity']}"
        listbox.insert(tk.END, display_text)

# Function to add the selected card to the database
def add_selected_card():
    selected_item = listbox.curselection()
    if not selected_item:
        messagebox.showwarning("Selection Error", "Please select a card from the search results.")
        return

    # Extract card details from selected text
    selected_text = listbox.get(selected_item[0])
    parts = selected_text.split(" - ")
    if len(parts) < 3:
        return

    card_name = parts[0].strip()
    set_name = parts[1].strip().split(" (#")[0]
    card_number = parts[1].split(" (#")[1].split(")")[0]
    rarity = parts[2].strip()

    # Retrieve the full card data including market price from the API
    cards_data = search_pokemon_cards(card_name, set_name)
    selected_card_data = next(
        (card for card in cards_data if card["set_name"] == set_name and card["card_number"] == card_number), None
    )

    if not selected_card_data:
        messagebox.showwarning("Data Error", "Could not retrieve price data for the selected card.")
        return

    market_price = selected_card_data["market_price"] if selected_card_data["market_price"] is not None else 0.0

    # Insert into DB
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO pokemon_cards (name, set_name, card_number, rarity, value)
                VALUES (?, ?, ?, ?, ?)
            ''', (card_name, set_name, card_number, rarity, market_price))
            conn.commit()
            messagebox.showinfo("Success", f"Added {card_name} ({set_name} #{card_number}) with price ${market_price:.2f} to My List!")
            update_listbox()
        except sqlite3.IntegrityError:
            messagebox.showwarning("Duplicate", f"{card_name} from {set_name} (#{card_number}) is already in My List!")

# Function to update "My List" in Listbox
def update_listbox():
    listbox_my_list.delete(0, tk.END)
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name, set_name, card_number, rarity, value FROM pokemon_cards")
        for row in cursor.fetchall():
            listbox_my_list.insert(tk.END, f"{row[0]} - {row[1]} (#{row[2]}) - {row[3]} - ${row[4]:.2f}")

# Function to remove a selected card from database
def remove_card():
    selected_item = listbox_my_list.curselection()
    if not selected_item:
        messagebox.showwarning("Selection Error", "Please select a card to remove.")
        return

    selected_text = listbox_my_list.get(selected_item[0])
    card_name = selected_text.split(" - ")[0]

    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM pokemon_cards WHERE name = ?", (card_name,))
        conn.commit()
    
    messagebox.showinfo("Removed", f"{card_name} removed from My List!")
    update_listbox()

# Function to update the Set Dropdown dynamically
def update_set_dropdown():
    set_dropdown["values"] = get_all_sets()

# --- GUI Setup ---
root = tk.Tk()
root.title("Pokémon Card Manager")
root.geometry("600x550")

# Create Notebook (Tabs)
notebook = ttk.Notebook(root)
notebook.pack(expand=True, fill="both")

# ---- Search & Add Card Tab ----
search_frame = ttk.Frame(notebook)
notebook.add(search_frame, text="Search & Add Card")

ttk.Label(search_frame, text="Search Pokémon Name:").pack(pady=5)
search_entry = ttk.Entry(search_frame, width=40)
search_entry.pack(pady=5)

# Set Dropdown (Updated Dynamically)
ttk.Label(search_frame, text="Filter by Set:").pack(pady=5)
set_var = tk.StringVar(value="All Sets")
set_dropdown = ttk.Combobox(search_frame, textvariable=set_var, state="readonly")
set_dropdown.pack(pady=5)
set_dropdown.bind("<Button-1>", lambda e: update_set_dropdown())  # Update when clicked

search_button = ttk.Button(search_frame, text="Search", command=search_card)
search_button.pack(pady=5)

listbox = tk.Listbox(search_frame, width=60, height=10)
listbox.pack(pady=5)

add_button = ttk.Button(search_frame, text="Add to My List", command=add_selected_card)
add_button.pack(pady=5)

# ---- My List Tab ----
list_frame = ttk.Frame(notebook)
notebook.add(list_frame, text="My List")

listbox_my_list = tk.Listbox(list_frame, width=60, height=15)
listbox_my_list.pack(padx=10, pady=10)

remove_button = ttk.Button(list_frame, text="Remove Selected", command=remove_card)
remove_button.pack(pady=5)

# Load existing data
create_table()
update_listbox()

# Run the main loop
root.mainloop()
