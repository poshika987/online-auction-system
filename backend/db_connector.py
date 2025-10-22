# db_connector.py

import mysql.connector
from mysql.connector import pooling
import os
from dotenv import load_dotenv

load_dotenv()

DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASSWORD = os.getenv('DB_PASSWORD') #CHANGE THIS
DB_NAME = 'auction'

try:
    db_pool = mysql.connector.pooling.MySQLConnectionPool(
        pool_name="auction_pool",
        pool_size=5,
        pool_reset_session=True,
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )
    print("Database connection pool created successfully.")

except mysql.connector.Error as e:
    print(f"Error creating connection pool: {e}")
    exit(1)


def get_connection():
    try:
        # Get a connection from the pool
        conn = db_pool.get_connection()
        
        if conn.is_connected():
            return conn
        else:
            print("Connection from pool is not valid.")
            return None

    except mysql.connector.Error as e:
        print(f"Error getting connection from pool: {e}")
        return None
