import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

print("pre")

try:
    mydb = pymysql.connect(
        host="127.0.0.1",
        user=os.getenv('DB_USERNAME'),
        password=os.getenv('DB_PASSWORD'),
        database="dkpbot"
    )
    print("post")
except Exception as err:
    print(f"Connection error: {err}")
