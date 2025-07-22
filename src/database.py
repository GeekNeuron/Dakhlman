
# src/database.py
import sqlite3
import os
import bcrypt
from datetime import datetime

DB_FILE = "dakhlman_data.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def setup_database():
    """ایجاد یا به‌روزرسانی جداول اولیه در پایگاه داده"""
    if os.path.exists(DB_FILE):
        # اینجا می‌توانید در آینده منطق مهاجرت (migration) دیتابیس را اضافه کنید
        return

    print("Creating database for the first time...")
    conn = get_db_connection()
    cursor = conn.cursor()

    # جدول تنظیمات (برای ذخیره رمز عبور)
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
            type TEXT NOT NULL, -- 'income', 'expense', 'transfer'
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
    default_categories = ['خوراک', 'حمل و نقل', 'مسکن', 'حقوق', 'تفریح']
    for cat in default_categories:
        cursor.execute("INSERT INTO categories (name) VALUES (?)", (cat,))
    
    cursor.execute("INSERT INTO accounts (name, balance) VALUES (?, ?)", ("کیف پول نقدی", 0.0))
    
    conn.commit()
    conn.close()

# --- توابع مربوط به امنیت ---
def set_password(password):
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    conn = get_db_connection()
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", ('password_hash', hashed))
    conn.commit()
    conn.close()

def check_password(password):
    conn = get_db_connection()
    stored_hash = conn.execute("SELECT value FROM settings WHERE key = 'password_hash'").fetchone()
    conn.close()
    if not stored_hash or not stored_hash['value']:
        return True # رمزی تنظیم نشده است
    return bcrypt.checkpw(password.encode('utf-8'), stored_hash['value'])

def is_password_set():
    if not os.path.exists(DB_FILE):
        return False
    conn = get_db_connection()
    res = conn.execute("SELECT value FROM settings WHERE key = 'password_hash'").fetchone()
    conn.close()
    return res is not None and res['value'] is not None

# --- توابع مربوط به داده‌ها ---
# (در یک پروژه واقعی، توابع بیشتری برای هر عملیات CRUD اضافه می‌شود)
def get_data_for_export():
    """داده‌ها را برای خروجی گرفتن آماده می‌کند"""
    conn = get_db_connection()
    query = """
        SELECT 
            t.transaction_date as 'تاریخ',
            a.name as 'حساب',
            CASE t.type 
                WHEN 'income' THEN 'درآمد' 
                WHEN 'expense' THEN 'هزینه'
                ELSE 'انتقال' 
            END as 'نوع',
            t.amount as 'مبلغ',
            c.name as 'دسته',
            t.description as 'شرح'
        FROM transactions t
        JOIN accounts a ON t.account_id = a.id
        LEFT JOIN categories c ON t.category_id = c.id
        ORDER BY t.transaction_date DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df
