import sqlite3
import os

db_path = "rescue_system.db"
if not os.path.exists(db_path):
    print("Database file not found!")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("--- USERS ---")
cursor.execute("SELECT id, username, role, is_active FROM users")
for row in cursor.fetchall():
    print(row)

print("\n--- COMPANIES ---")
cursor.execute("SELECT id, company_name, status, is_verified FROM rescue_companies")
for row in cursor.fetchall():
    print(row)

conn.close()
