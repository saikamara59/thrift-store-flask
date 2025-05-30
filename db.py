# db.py
import os, psycopg2, psycopg2.extras
from dotenv import load_dotenv
load_dotenv()

def get_db_connection():
    connection = psycopg2.connect(
        host='localhost',
        database='thrift_store_db',
        user=os.getenv('POSTGRES_USERNAME'),
        password=os.getenv('POSTGRES_PASSWORD')
    )
    return connection
