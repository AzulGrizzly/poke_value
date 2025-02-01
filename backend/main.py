import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
import requests
from datetime import datetime
from pokemon_api import search_pokemon_cards, get_all_sets
import os

# Database file
DB_FILE = "pokemon.db"
SESSION_FILE = "session.txt"  # File to track logged-in user

# 🔹 Get logged-in user from session file
if not os.path.exists(SESSION_FILE):
    messagebox.showerror("Error", "No user session found. Please log in.")
    exit()

with open(SESSION_FILE, "r") as f:
    current_user = f.read().strip()


# GitHub Config
GITHUB_USER = "azulgrizzly"
REPO_NAME = "poke_value"
BRANCH = "master"

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
            commit_messages.append({
                "date": commit_date,
                "message": message
            })

        return commit_messages

    except requests.exceptions.RequestException as e:
        return [{"date": "Error", "message": f"Error fetching updates: {e}"}]

# Function to show full commit details in a popup
def show_commit_details(event):
    """Opens a modal window with the full commit message when double-clicked."""
    selected_index = updates_listbox.curselection()
    if not selected_index:
        return

    selected_commit = commit_data[selected_index[0]]
    commit_date = selected_commit["date"]
    commit_message = selected_commit["message"]

    popup = tk.Toplevel(root)
    popup.title("Commit Details")
    popup.geometry("500x300")

    ttk.Label(popup, text="Commit Date:", font=("Arial", 10, "bold")).pack(pady=5)
    ttk.Label(popup, text=commit_date, wraplength=450).pack(pady=5)

    ttk.Label(popup, text="Commit Message:", font=("Arial", 10, "bold")).pack(pady=5)
    
    message_text = tk.Text(popup, wrap="word", height=10, width=50)
    message_text.insert("1.0", commit_message)
    message_text.config(state=tk.DISABLED)
    message_text.pack(pady=5)

    ttk.Button(popup, text="Close", command=popup.destroy).pack(pady=5)

# Function to update commit history in "App Updates" tab
def update_commit_list():
    updates_listbox.delete(0, tk.END)
    global commit_data
    commit_data = fetch_commit_history()
    
    for commit in commit_data:
        updates_listbox.insert(tk.END, f"{commit['date']} - {commit['message'][:50]}...")  # Show preview

# Function to search for a Pokémon card using the API
def search_card():
    search_query = search_entry.get().strip()
    selected_set = set_var.get()

    if not search_query:
        messagebox.showwarning("Input Error", "Please enter a Pokémon name.")
        return

    search_button.config(state=tk.DISABLED, text="Searching...")
    root.update_idletasks()

    listbox.delete(0, tk.END)

    results = search_pokemon_cards(search_query, selected_set)

    search_button.config(state=tk.NORMAL, text="Search")

    if not results:
        messagebox.showinfo("No Results", f"No cards found for '{search_query}' in '{selected_set}'.")
        return

    for card in results:
        display_text = f"{card['name']} - {card['set_name']} (#{card['card_number']}) - {card['rarity']}"
        listbox.insert(tk.END, display_text)

# Function to add a selected card to the database
# Function to add a selected card to the database
def add_selected_card():
    selected_item = listbox.curselection()
    if not selected_item:
        messagebox.showwarning("Selection Error", "Please select a card from the search results.")
        return

    selected_text = listbox.get(selected_item[0])
    parts = selected_text.split(" - ")
    if len(parts) < 3:
        return

    card_name = parts[0].strip()
    set_name = parts[1].split(" (#")[0].strip()
    card_number = parts[1].split(" (#")[1].split(")")[0].strip()
    rarity = parts[2].strip()

    # 🔹 Fetch Full Card Data Including Price from API
    cards_data = search_pokemon_cards(card_name, set_name)
    selected_card_data = next(
        (card for card in cards_data if card["set_name"] == set_name and card["card_number"] == card_number),
        None
    )

    if not selected_card_data:
        messagebox.showwarning("Data Error", "Could not retrieve price data for the selected card.")
        return

    # 🔹 Extract Market Price from API Response
    market_price = selected_card_data["market_price"] if selected_card_data["market_price"] is not None else 0.0

    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO pokemon_cards (name, set_name, card_number, rarity, value, username)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (card_name, set_name, card_number, rarity, market_price, current_user))
            conn.commit()
            messagebox.showinfo("Success", f"Added {card_name} ({set_name} #{card_number}) with price ${market_price:.2f} to My List!")
            update_listbox()
        except sqlite3.IntegrityError:
            messagebox.showwarning("Duplicate", f"{card_name} from {set_name} (#{card_number}) is already in My List!")



# Function to update "My List" (Filtered by logged-in user)
def update_listbox():
    listbox_my_list.delete(0, tk.END)  # Clear previous entries

    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name, set_name, card_number, rarity, value FROM pokemon_cards WHERE username = ?", (current_user,))
        user_cards = cursor.fetchall()

    if not user_cards:
        listbox_my_list.insert(tk.END, "No Pokémon found for this user.")
        return

    for row in user_cards:
        listbox_my_list.insert(tk.END, f"{row[0]} - {row[1]} (#{row[2]}) - {row[3]} - ${row[4]:.2f}")

# Function to remove a selected card from "My List"
def remove_card():
    selected_item = listbox_my_list.curselection()
    if not selected_item:
        messagebox.showwarning("Selection Error", "Please select a card to remove.")
        return

    selected_text = listbox_my_list.get(selected_item[0])
    card_name = selected_text.split(" - ")[0]

    confirm = messagebox.askyesno("Confirm Deletion", f"Are you sure you want to remove '{card_name}'?")

    if confirm:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM pokemon_cards WHERE name = ?", (card_name,))
            conn.commit()

        messagebox.showinfo("Removed", f"{card_name} removed from My List!")
        update_listbox()
        
# Function to log out (clears session & returns to auth)
def logout():
    os.remove(SESSION_FILE)
    messagebox.showinfo("Logged Out", "You have been logged out.")
    root.destroy()
    os.system("python auth.py")  # Relaunch authentication window

# GUI Setup
root = tk.Tk()
root.title("Pokémon Card Manager")
root.geometry("700x600")

notebook = ttk.Notebook(root)
notebook.pack(expand=True, fill="both")

# Search & Add Tab
search_frame = ttk.Frame(notebook)
notebook.add(search_frame, text="Search & Add Card")

ttk.Label(search_frame, text="Search Pokémon Name:").pack(pady=5)
search_entry = ttk.Entry(search_frame, width=40)
search_entry.pack(pady=5)

ttk.Label(search_frame, text="Filter by Set:").pack(pady=5)
set_var = tk.StringVar(value="All Sets")
set_dropdown = ttk.Combobox(search_frame, textvariable=set_var, state="readonly")
set_dropdown.pack(pady=5)

search_entry.bind("<Return>", lambda event: search_card())

search_button = ttk.Button(search_frame, text="Search", command=search_card)
search_button.pack(pady=5)

listbox = tk.Listbox(search_frame, width=80, height=10)
listbox.pack(pady=5)

add_button = ttk.Button(search_frame, text="Add to My List", command=add_selected_card)
add_button.pack(pady=5)

# My List Tab
list_frame = ttk.Frame(notebook)
notebook.add(list_frame, text="My List")

listbox_my_list = tk.Listbox(list_frame, width=80, height=15)
listbox_my_list.pack(padx=10, pady=10)

remove_button = ttk.Button(list_frame, text="Remove Selected", command=remove_card)
remove_button.pack(pady=5)

# App Updates Tab
updates_frame = ttk.Frame(notebook)
notebook.add(updates_frame, text="App Updates")

updates_listbox = tk.Listbox(updates_frame, width=80, height=15)
updates_listbox.pack(pady=5, padx=10)
updates_listbox.bind("<Double-Button-1>", show_commit_details)

refresh_button = ttk.Button(updates_frame, text="Refresh Updates", command=update_commit_list)
refresh_button.pack(pady=5)

# 🔹 Logout Button
logout_button = ttk.Button(root, text="Logout", command=logout)
logout_button.pack(pady=10)

create_table()
update_listbox()
update_commit_list()
root.mainloop()
