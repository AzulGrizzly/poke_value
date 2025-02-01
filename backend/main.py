import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
import requests
from datetime import datetime
from pokemon_api import search_pokemon_cards, get_all_sets

# Database file
DB_FILE = "pokemon.db"

# GitHub Config
GITHUB_USER = "azulgrizzly"
REPO_NAME = "poke_value"
BRANCH = "master" 

# Function to fetch GitHub commit history
def fetch_commit_history():
    """Fetches the latest commits from GitHub and returns a list of commit messages with dates."""
    url = f"https://api.github.com/repos/{GITHUB_USER}/{REPO_NAME}/commits?sha={BRANCH}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        commits = response.json()

        commit_messages = []
        for commit in commits[:10]:  # Limit to last 10 commits
            date_str = commit["commit"]["committer"]["date"]
            commit_date = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d %H:%M")
            message = commit["commit"]["message"]
            commit_messages.append(f"{commit_date} - {message}")

        return commit_messages

    except requests.exceptions.RequestException as e:
        return [f"Error fetching updates: {e}"]

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

    # Disable Search Button & Show Loading Indicator
    search_button.config(state=tk.DISABLED, text="Searching...")

    # Clear previous search results
    listbox.delete(0, tk.END)
    root.update_idletasks()  # Force UI to refresh

    # Fetch matching cards from API with set filter
    results = search_pokemon_cards(search_query, selected_set)

    # Restore Button State After API Call
    search_button.config(state=tk.NORMAL, text="Search")

    if not results:
        messagebox.showinfo("No Results", f"No cards found for '{search_query}' in '{selected_set}'.")
        return

    # Populate Listbox with results
    for card in results:
        display_text = f"{card['name']} - {card['set_name']} (#{card['card_number']}) - {card['rarity']}"
        listbox.insert(tk.END, display_text)

# Function to update the Set Dropdown dynamically
def update_set_dropdown():
    set_dropdown["values"] = get_all_sets()

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

    # Show confirmation popup
    confirm = messagebox.askyesno("Confirm Deletion", f"Are you sure you want to remove '{card_name}'?")

    if confirm:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM pokemon_cards WHERE name = ?", (card_name,))
            conn.commit()
        
        messagebox.showinfo("Removed", f"{card_name} removed from My List!")
        update_listbox()

# Function to update commit history in "App Updates" tab
def update_commit_list():
    updates_listbox.delete(0, tk.END)
    commits = fetch_commit_history()
    
    for commit in commits:
        updates_listbox.insert(tk.END, commit)

# --- GUI Setup ---
root = tk.Tk()
root.title("Pokémon Card Manager")
root.geometry("600x600")

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

search_entry.bind("<Return>", lambda event: search_card())

search_button = ttk.Button(search_frame, text="Search", command=search_card)
search_button.pack(pady=5)

listbox = tk.Listbox(search_frame, width=60, height=10)
listbox.pack(pady=5)

# ---- My List Tab ----
list_frame = ttk.Frame(notebook)
notebook.add(list_frame, text="My List")

listbox_my_list = tk.Listbox(list_frame, width=60, height=15)
listbox_my_list.pack(padx=10, pady=10)

remove_button = ttk.Button(list_frame, text="Remove Selected", command=remove_card)
remove_button.pack(pady=5)

# ---- App Updates Tab ----
updates_frame = ttk.Frame(notebook)
notebook.add(updates_frame, text="App Updates")

ttk.Label(updates_frame, text="Latest GitHub Updates:", font=("Arial", 12, "bold")).pack(pady=5)

updates_listbox = tk.Listbox(updates_frame, width=80, height=15)
updates_listbox.pack(pady=5, padx=10)

refresh_button = ttk.Button(updates_frame, text="Refresh Updates", command=update_commit_list)
refresh_button.pack(pady=5)

# Load existing data
create_table()
update_listbox()
update_commit_list()  # Load commits on startup

# Run the main loop
root.mainloop()
