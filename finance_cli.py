import os
import sqlite3
import hashlib
from datetime import datetime

# === DATABASE SETUP ===
APP_DIR = os.path.join(os.path.expanduser("~"), ".pfinance")
os.makedirs(APP_DIR, exist_ok=True)
DB_PATH = os.path.join(APP_DIR, "pfinance.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()

    # Users table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL
    )
    """)

    # Transactions table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        type TEXT NOT NULL CHECK(type IN ('income', 'expense')),
        category TEXT NOT NULL,
        amount REAL NOT NULL,
        date TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)

    # Budgets table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS budgets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        category TEXT NOT NULL,
        monthly_limit REAL NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)

    conn.commit()
    conn.close()


# === AUTHENTICATION ===
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def register(username, password):
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
                    (username, hash_password(password)))
        conn.commit()
        print(f"✅ User '{username}' registered successfully.")
    except sqlite3.IntegrityError:
        print("❌ Username already exists.")
    finally:
        conn.close()


def login(username, password):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, password_hash FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    conn.close()

    if row and row["password_hash"] == hash_password(password):
        print(f"✅ Logged in as '{username}'.")
        return row["id"]
    else:
        print("❌ Invalid username or password.")
        return None


# === TRANSACTIONS ===
def add_transaction(user_id, t_type, category, amount):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO transactions (user_id, type, category, amount, date)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, t_type, category, amount, datetime.now().strftime("%Y-%m-%d")))
    conn.commit()
    conn.close()
    print(f"✅ {t_type.capitalize()} of {amount} in '{category}' added.")


def view_report(user_id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT type, SUM(amount) as total FROM transactions
        WHERE user_id = ?
        GROUP BY type
    """, (user_id,))
    totals = {row["type"]: row["total"] for row in cur.fetchall()}

    income = totals.get("income", 0)
    expense = totals.get("expense", 0)
    savings = income - expense

    print("\n📊 Financial Report")
    print(f"Total Income : {income}")
    print(f"Total Expense: {expense}")
    print(f"Savings      : {savings}\n")

    conn.close()


# === MAIN CLI ===
def main():
    init_db()
    user_id = None

    while True:
        if not user_id:
            print("\n1. Register")
            print("2. Login")
            print("3. Exit")
            choice = input("Choose an option: ")

            if choice == "1":
                u = input("Username: ")
                p = input("Password: ")
                register(u, p)
            elif choice == "2":
                u = input("Username: ")
                p = input("Password: ")
                user_id = login(u, p)
            elif choice == "3":
                break
            else:
                print("❌ Invalid choice.")
        else:
            print("\n1. Add Income")
            print("2. Add Expense")
            print("3. View Report")
            print("4. Logout")
            choice = input("Choose an option: ")

            if choice == "1":
                cat = input("Category: ")
                amt = float(input("Amount: "))
                add_transaction(user_id, "income", cat, amt)
            elif choice == "2":
                cat = input("Category: ")
                amt = float(input("Amount: "))
                add_transaction(user_id, "expense", cat, amt)
            elif choice == "3":
                view_report(user_id)
            elif choice == "4":
                user_id = None
                print("✅ Logged out.")
            else:
                print("❌ Invalid choice.")


if __name__ == "__main__":
    main()
