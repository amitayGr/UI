"""
db_utils.py
-----------
Description:
    Database utility functions for the Geometric Learning System. This module handles
    all database connections and user authentication operations, providing a clean
    interface for database interactions throughout the application.

Main Components:
    - Database Connection Management
    - User Authentication
    - User Creation and Management
    - Password Hashing and Verification

Author: Karin Hershko and Afik Dadon
Date: February 2025
"""

import pyodbc
from db_config import DB_CONFIG
from extensions import bcrypt
from typing import Optional, Dict


def get_db_connection():
    """Create and return a connection to the database using configuration parameters."""
    conn_str = (
        f"DRIVER={{{DB_CONFIG['driver']}}};"
        f"SERVER={DB_CONFIG['server']};"
        f"DATABASE={DB_CONFIG['database']};"
        f"Trusted_Connection={DB_CONFIG['trusted_connection']};"
    )
    return pyodbc.connect(conn_str)


# Hash password לפני שמכניסים ל‑DB
def hash_password(password: str) -> str:
    """Hash a password using Flask-Bcrypt."""
    return bcrypt.generate_password_hash(password).decode('utf-8')  # חובה decode ל־utf-8

# Verify password
def verify_user(email: str, password: str) -> Optional[Dict]:
    password = password.strip()
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT user_id, first_name, last_name, email, password_hash, role 
                FROM Users 
                WHERE email = ?""", (email,))
            user = cursor.fetchone()
            print("Fetched user:", user)

            if user:
                print("DB password_hash:", user[4])
                print("Password entered:", password)

                result = bcrypt.check_password_hash(user[4], password)
                print("check_password_hash result:", result)
                if result :
                    return {
                        'user_id': user[0],
                        'first_name': user[1],
                        'last_name': user[2],
                        'email': user[3],
                        'role': user[5]
                    }

            return None
    except Exception as e:
        print(f"Database error in verify_user: {str(e)}")
        return None

def create_user(first_name: str, last_name: str, email: str, password: str) -> bool:
    """Create a new user in the database with hashed password."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Check for existing user
            cursor.execute("SELECT email FROM Users WHERE email = ?", (email,))
            if cursor.fetchone():
                return False

            # Hash the password BEFORE inserting
            hashed_pw = password
            print("original pass:", password)
            print("hashed_pw:", hashed_pw)

            # Insert new user
            cursor.execute(
                """INSERT INTO Users (first_name, last_name, email, password_hash, role, created_at) 
                   VALUES (?, ?, ?, ?, 'user', GETDATE())""",
                (first_name, last_name, email, hashed_pw)
            )
            conn.commit()
            return True

    except Exception as e:
        print(f"Database error in create_user: {str(e)}")

        return False

def verify_email_exists(email: str) -> bool:
    """Check if an email address already exists in the database."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT user_id FROM Users WHERE email = ?', (email,))
            return bool(cursor.fetchone())

    except Exception as e:
        print(f"Database error in verify_email_exists: {str(e)}")
        return False

def update_last_login(user_id: int) -> None:
    """Update the last login timestamp for a user in the database."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE Users 
                SET last_login = CURRENT_TIMESTAMP
                WHERE user_id = ?""", (user_id,))
            conn.commit()
    except Exception as e:
        print(f"Error updating last login: {str(e)}")


# 🔹 בדיקה שה-hash עובד
pw = "סיסמה_שלך_לבדיקה"
hash_pw = hash_password(pw)
print("Generated hash:", hash_pw)
print("Check:", bcrypt.check_password_hash(hash_pw, pw))  # חייב להחזיר True
