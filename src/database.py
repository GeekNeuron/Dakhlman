# src/database.py
import sqlite3
import os
import bcrypt
from datetime import datetime

DB_FILE = "dakhlman_data.db"

def get_db_connection():
    """یک اتصال جدید به پایگاه داده ایجاد کرده و برمی‌گرداند."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def setup_database():
    """جداول اولیه را در اولین اجرای برنامه ایجاد می‌کند."""
    if os.path.exists(DB_FILE):
        # در آینده می‌توان منطق به‌روزرسانی ساختار دیتابیس (migration) را اینجا اضافه کرد.
        return
    
    print("Creating database for the first time...")
    conn = get_db_connection()
    cursor = conn.cursor()

    # جدول تنظیمات برای ذخیره رمز عبور
    cursor.execute("CREATE TABLE settings (key TEXT PRIMARY KEY, value BLOB)")
    
    # جدول حساب‌ها
    cursor.execute("""
        CREATE TABLE accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            balance REAL NOT NULL DEFAULT 0
        )
    """)
    
    # جدول دسته‌بندی‌ها
    cursor.execute("""
        CREATE TABLE categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            budget REAL DEFAULT 0
        )
    """)
    
    # جدول تراکنش‌ها
    cursor.execute("""
        CREATE TABLE transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL, -- 'income', 'expense', or 'transfer'
            amount REAL NOT NULL,
            description TEXT,
            transaction_date TEXT NOT NULL,
            category_id INTEGER,
            account_id INTEGER NOT NULL,
            FOREIGN KEY (category_id) REFERENCES categories (id),
            FOREIGN KEY (account_id) REFERENCES accounts (id)
        )
    """)
    
    # افزودن داده‌های پیش‌فرض
    default_categories = ['خوراک', 'حمل و نقل', 'مسکن', 'حقوق', 'تفریح', 'پوشاک', 'درمان']
    for cat in default_categories:
        cursor.execute("INSERT INTO categories (name) VALUES (?)", (cat,))
    
    cursor.execute("INSERT INTO accounts (name, balance) VALUES (?, ?)", ("کیف پول نقدی", 0.0))
    
    conn.commit()
    conn.close()

# --- توابع امنیت ---
def set_password(password: str):
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    conn = get_db_connection()
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", ('password_hash', hashed))
    conn.commit()
    conn.close()

def check_password(password: str) -> bool:
    conn = get_db_connection()
    result = conn.execute("SELECT value FROM settings WHERE key = 'password_hash'").fetchone()
    conn.close()
    if not result or not result['value']:
        return True # رمزی تنظیم نشده است
    return bcrypt.checkpw(password.encode('utf-8'), result['value'])

def is_password_set() -> bool:
    if not os.path.exists(DB_FILE):
        return False
    conn = get_db_connection()
    res = conn.execute("SELECT value FROM settings WHERE key = 'password_hash'").fetchone()
    conn.close()
    return res is not None and res['value'] is not None

# --- توابع حساب‌ها ---
def get_accounts():
    conn = get_db_connection()
    accounts = conn.execute("SELECT * FROM accounts ORDER BY name").fetchall()
    conn.close()
    return accounts

def add_account(name: str, initial_balance: float = 0.0):
    conn = get_db_connection()
    try:
        conn.execute("INSERT INTO accounts (name, balance) VALUES (?, ?)", (name, initial_balance))
        conn.commit()
    except sqlite3.IntegrityError:
        return False # نام حساب تکراری است
    finally:
        conn.close()
    return True

# --- توابع دسته‌بندی‌ها ---
def get_categories():
    conn = get_db_connection()
    categories = conn.execute("SELECT * FROM categories ORDER BY name").fetchall()
    conn.close()
    return categories

def add_category(name: str):
    conn = get_db_connection()
    try:
        conn.execute("INSERT INTO categories (name) VALUES (?)", (name,))
        conn.commit()
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()
    return True
    
# --- توابع تراکنش‌ها ---
def add_transaction(type: str, amount: float, desc: str, date: str, cat_id: int, acc_id: int):
    conn = get_db_connection()
    conn.execute("""
        INSERT INTO transactions (type, amount, description, transaction_date, category_id, account_id)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (type, amount, desc, date, cat_id, acc_id))
    conn.commit()
    conn.close()
    
    # به‌روزرسانی موجودی حساب
    if type == 'income':
        update_account_balance(acc_id, amount)
    elif type == 'expense':
        update_account_balance(acc_id, -amount)

def update_account_balance(account_id: int, amount_change: float):
    conn = get_db_connection()
    conn.execute("UPDATE accounts SET balance = balance + ? WHERE id = ?", (amount_change, account_id))
    conn.commit()
    conn.close()

def execute_transfer(from_acc_id: int, to_acc_id: int, amount: float, desc: str, date: str):
    # کسر از حساب مبدأ
    update_account_balance(from_acc_id, -amount)
    # افزودن به حساب مقصد
    update_account_balance(to_acc_id, amount)

    # ثبت دو تراکنش برای ردگیری
    conn = get_db_connection()
    # هزینه از مبدأ
    conn.execute("""
        INSERT INTO transactions (type, amount, description, transaction_date, account_id)
        VALUES ('transfer', ?, ?, ?, ?)
    """, (amount, f"انتقال به {get_account_name(to_acc_id)}: {desc}", date, from_acc_id))
    # درآمد به مقصد
    conn.execute("""
        INSERT INTO transactions (type, amount, description, transaction_date, account_id)
        VALUES ('transfer', ?, ?, ?, ?)
    """, (amount, f"دریافت از {get_account_name(from_acc_id)}: {desc}", date, to_acc_id))
    conn.commit()
    conn.close()

def get_account_name(account_id: int) -> str:
    # یک تابع کمکی برای گرفتن نام حساب
    conn = get_db_connection()
    name = conn.execute("SELECT name FROM accounts WHERE id = ?", (account_id,)).fetchone()['name']
    conn.close()
    return name
