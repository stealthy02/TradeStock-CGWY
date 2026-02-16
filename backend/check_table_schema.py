import sqlite3

conn = sqlite3.connect('easy_stock_db.db')
cursor = conn.cursor()

print('t_sale_statement table schema:')
cursor.execute("PRAGMA table_info(t_sale_statement)")
for row in cursor.fetchall():
    print(row)

conn.close()