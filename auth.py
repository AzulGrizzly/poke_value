import os
import subprocess
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
import bcrypt
import sys


DB_FILE = "pokemon.db"
SESSION_FILE = "session.txt"

# Automatically find the backend directory
BACKEND_DIR = os.path.join(os.path.dirname(__file__), "backend")
MAIN_PY_PATH = os.path.join(BACKEND_DIR, "main.py")

# Function to hash passwords before storing them
def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

# Function to verify passwords
def check_password(stored_password, entered_password):
    return bcrypt.checkpw(entered_password.encode(), stored_password.encode())

# Function to register a new user
def register_user(username, password):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        try:
            hashed_pw = hash_password(password)
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_pw))
            conn.commit()
            messagebox.showinfo("Success", "Account created successfully! You can now log in.")
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Username already exists. Try another one.")

# Function to verify user login
def login_user(username, password):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
        user_data = cursor.fetchone()

        if user_data and check_password(user_data[0], password):
            messagebox.showinfo("Login Successful", f"Welcome, {username}!")

            # 🔹 Save logged-in user to session file
            with open(SESSION_FILE, "w") as f:
                f.write(username)

            root.destroy()  # Close login window

            # 🔹 Launch `main.py` dynamically
            subprocess.Popen([sys.executable, MAIN_PY_PATH])

        else:
            messagebox.showerror("Login Failed", "Invalid username or password.")

# UI for Login/Signup
def show_auth_window():
    global root
    root = tk.Tk()
    root.title("Login or Register")
    root.geometry("400x300")

    notebook = ttk.Notebook(root)
    notebook.pack(expand=True, fill="both")

    # 🔹 Login Tab
    login_frame = ttk.Frame(notebook)
    notebook.add(login_frame, text="Login")

    ttk.Label(login_frame, text="Username:").pack(pady=5)
    login_username_entry = ttk.Entry(login_frame, width=30)
    login_username_entry.pack(pady=5)

    ttk.Label(login_frame, text="Password:").pack(pady=5)
    login_password_entry = ttk.Entry(login_frame, width=30, show="*")
    login_password_entry.pack(pady=5)

    login_button = ttk.Button(login_frame, text="Login", command=lambda: login_user(login_username_entry.get(), login_password_entry.get()))
    login_button.pack(pady=10)

    # 🔹 Register Tab
    register_frame = ttk.Frame(notebook)
    notebook.add(register_frame, text="Register")

    ttk.Label(register_frame, text="Username:").pack(pady=5)
    register_username_entry = ttk.Entry(register_frame, width=30)
    register_username_entry.pack(pady=5)

    ttk.Label(register_frame, text="Password:").pack(pady=5)
    register_password_entry = ttk.Entry(register_frame, width=30, show="*")
    register_password_entry.pack(pady=5)

    register_button = ttk.Button(register_frame, text="Register", command=lambda: register_user(register_username_entry.get(), register_password_entry.get()))
    register_button.pack(pady=10)

    root.mainloop()

# Run the authentication UI
if __name__ == "__main__":
    show_auth_window()

