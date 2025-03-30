import hashlib
import threading


def o():
    with open(r"C:\Users\Emilien\Bureau\tiktok_astronovas_7450580654208650501.mp4", 'rb') as f:
        print(hashlib.file_digest(f, 'sha256').hexdigest())


for i in range(2000):
    threading.Thread(target=o, daemon=False).start()
    
