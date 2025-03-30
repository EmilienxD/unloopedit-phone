import pg8000

conn = pg8000.connect(
    user="postgres",
    password="",
    host="db.annedegwrqpudigispmy.supabase.co",
    database="postgres"
)
cursor = conn.cursor()

cursor.execute('''SELECT * FROM "VideoData";''')
print(cursor.fetchall())

cursor.close()
conn.close()
