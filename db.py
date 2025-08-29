import sqlite3

# Keep your original database connection exactly as it was
conn = sqlite3.connect('volunteer.db', check_same_thread=False, isolation_level=None)
db = conn.cursor()
