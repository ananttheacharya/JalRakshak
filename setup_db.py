import mysql.connector
from mysql.connector import Error
import os

# Default config for the new user we want to create
APP_USER = "jalrakshak"
APP_PASS = "jalrakshak123"
DB_NAME = "jalrakshak"

def setup_database():
    print("--- JalRakshak Database Setup ---")
    print("This script will create the database, user, schema, and seed data.")
    
    # Connect as root to create DB and User
    root_user = input("Enter MySQL root user (default: root): ") or "root"
    root_pass = input("Enter MySQL root password: ")

    try:
        conn = mysql.connector.connect(
            host="localhost",
            user=root_user,
            password=root_pass
        )
        cursor = conn.cursor()

        # 1. Create Database
        print(f"Creating database '{DB_NAME}'...")
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")

        # 2. Create User and Grant Privileges
        print(f"Creating user '{APP_USER}'...")
        # Note: This syntax works for MySQL 8.x
        cursor.execute(f"CREATE USER IF NOT EXISTS '{APP_USER}'@'localhost' IDENTIFIED BY '{APP_PASS}'")
        cursor.execute(f"GRANT ALL PRIVILEGES ON {DB_NAME}.* TO '{APP_USER}'@'localhost'")
        cursor.execute("FLUSH PRIVILEGES")
        
        print("Database and User verified.")
        cursor.close()
        conn.close()

        # 3. Import Schema and Seed using the new user
        # Re-connect as the app user
        conn = mysql.connector.connect(
            host="localhost",
            user=APP_USER,
            password=APP_PASS,
            database=DB_NAME,
            multi_statements=True
        )
        cursor = conn.cursor()

        # Helper to execute sql file
        def execute_sql_file(filename):
            print(f"Executing {filename}...")
            with open(filename, 'r') as f:
                sql_file = f.read()
                # Split by semicolon is naive but works for simple dumps usually
                # better to use iterator if supported or simple execute
                for result in cursor.execute(sql_file, multi=True):
                    pass
            conn.commit()
            print(f"Successfully executed {filename}.")

        # Execute Schema
        execute_sql_file('db/schema.sql')
        
        # Execute Seed
        execute_sql_file('db/seed.sql')

        print("\n--- Setup Complete! ---")
        print("You can now run the dashboard and simulator.")

    except Error as e:
        print(f"\n[ERROR] Database setup failed: {e}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            conn.close()

if __name__ == "__main__":
    setup_database()
