import sqlite3
conn = sqlite3.connect('shadowlink.db')
print(conn.execute('SELECT relationship_type, COUNT(*) FROM trust_links GROUP BY relationship_type').fetchall())
