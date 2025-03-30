
import pg8000

conn = pg8000.connect(
    user="postgres",
    password="",
    host="db.zumcamsmeopgriiybhoz.supabase.co",
    database="postgres"
)

cursor = conn.cursor()

sql = """
SELECT * FROM "VideoData"
"""

cursor.execute(sql)
print(cursor.fetchall())
conn.commit()
