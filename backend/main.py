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

    # Create a popup window
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

# Function to search for a Pokémon card using the API
def search_card():
    search_query = search_entry.get().strip()
    selected_set = set_var.get()

    if not search_query:
        messagebox.showwarning("Input Error", "Please enter a Pokémon name.")
        return

    # Disable Search Button & Show Loading Indicator
    search_button.config(state=tk.DISABLED, text="Searching...")
    root.update_idletasks()  # Force UI to refresh

    # Clear previous search results
    listbox.delete(0, tk.END)

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

# Function to update commit history in "App Updates" tab
def update_commit_list():
    updates_listbox.delete(0, tk.END)
    global commit_data
    commit_data = fetch_commit_history()
    
    for commit in commit_data:
        updates_listbox.insert(tk.END, f"{commit['date']} - {commit['message'][:50]}...")  # Show preview

# --- GUI Setup ---
root = tk.Tk()
root.title("Pokémon Card Manager")
root.geometry("700x600")

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

search_entry.bind("<Return>", lambda event: search_card())

search_button = ttk.Button(search_frame, text="Search", command=search_card)
search_button.pack(pady=5)

listbox = tk.Listbox(search_frame, width=80, height=10)
listbox.pack(pady=5)

# ---- My List Tab ----
list_frame = ttk.Frame(notebook)
notebook.add(list_frame, text="My List")

listbox_my_list = tk.Listbox(list_frame, width=80, height=15)
listbox_my_list.pack(padx=10, pady=10)

remove_button = ttk.Button(list_frame, text="Remove Selected", command=lambda: messagebox.showinfo("Feature Coming Soon", "Remove functionality not implemented yet."))
remove_button.pack(pady=5)

# ---- App Updates Tab ----
updates_frame = ttk.Frame(notebook)
notebook.add(updates_frame, text="App Updates")

ttk.Label(updates_frame, text="Latest GitHub Updates:", font=("Arial", 12, "bold")).pack(pady=5)

updates_listbox = tk.Listbox(updates_frame, width=80, height=15)
updates_listbox.pack(pady=5, padx=10)

# Bind double-click event to show full commit details
updates_listbox.bind("<Double-Button-1>", show_commit_details)

refresh_button = ttk.Button(updates_frame, text="Refresh Updates", command=update_commit_list)
refresh_button.pack(pady=5)

# Load commit history on startup
update_commit_list()

# Run the main loop
root.mainloop()
