import mysql.connector
from mysql.connector import pooling
import os
from dotenv import load_dotenv

load_dotenv()

DB_HOST = 'localhost'
DB_PASSWORD_ROOT = os.getenv('DB_PASSWORD') 
DB_NAME = 'auction'

USER_CREDENTIALS = {
    "user": "auction_user1",
    "password": "456"
}

ADMIN_CREDENTIALS = {
    "user": "auction_admin",
    "password": "123"
}

try:
    user_pool = mysql.connector.pooling.MySQLConnectionPool(
        pool_name="auction_user_pool",
        pool_size=5,
        pool_reset_session=True,
        host=DB_HOST,
        database=DB_NAME,
        user=USER_CREDENTIALS["user"],
        password=USER_CREDENTIALS["password"]
    )
    print("Database connection pool 'user_pool' created successfully.")

    admin_pool = mysql.connector.pooling.MySQLConnectionPool(
        pool_name="auction_admin_pool",
        pool_size=2,
        pool_reset_session=True,
        host=DB_HOST,
        database=DB_NAME,
        user=ADMIN_CREDENTIALS["user"],
        password=ADMIN_CREDENTIALS["password"]
    )
    print("Database connection pool 'admin_pool' created successfully.")

except mysql.connector.Error as e:
    print(f"Error creating connection pools: {e}")
    exit(1)


def get_user_connection():
    """Gets a connection from the limited 'auction_user' pool."""
    try:
        conn = user_pool.get_connection()
        if conn.is_connected():
            return conn
        else:
            return None
    except mysql.connector.Error as e:
        print(f"Error getting USER connection: {e}")
        return None

def get_admin_connection():
    """Gets a connection from the powerful 'auction_admin' pool."""
    try:
        conn = admin_pool.get_connection()
        if conn.is_connected():
            return conn
        else:
            return None
    except mysql.connector.Error as e:
        print(f"Error getting ADMIN connection: {e}")
        return None