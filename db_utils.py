"""
db_utils.py
-----------
Description:
    Database utility functions for the Geometric Learning System. This module handles
    user authentication operations for the UI application, while geometry learning
    operations are now handled through the API client for localhost:17654.

Main Components:
    - Database Connection Management (for user data)
    - User Authentication
    - User Creation and Management
    - Password Hashing and Verification

Note: Geometry learning data (questions, theorems, sessions) is now accessed
      through the API client (api_client.py) instead of direct database access.

Author: Karin Hershko and Afik Dadon
Date: February 2025
Updated: November 2025 - API Integration
"""

import pyodbc
from db_config import DB_CONFIG
from extensions import bcrypt
from typing import Optional, Dict


def get_db_connection():
    """
    Create and return a connection to the user database using configuration parameters.
    
    Note: This is used for user authentication data only. Geometry learning data
    is accessed through the API client.
    """
    conn_str = (
        f"DRIVER={{{DB_CONFIG['driver']}}};"
        f"SERVER={DB_CONFIG['server']};"
        f"DATABASE={DB_CONFIG['database']};"
        f"Trusted_Connection={DB_CONFIG['trusted_connection']};"
    )
    return pyodbc.connect(conn_str)


# Hash password לפני שמכניסים ל‑DB
def hash_password(password: str) -> str:
    """Hash a password using Flask-Bcrypt for user authentication."""
    return bcrypt.generate_password_hash(password).decode('utf-8')  # חובה decode ל־utf-8

# Verify password for user authentication
def verify_user(email: str, password: str) -> Optional[Dict]:
    """
    Verify user credentials for UI authentication.
    
    Note: This handles UI user authentication only. Geometry learning sessions
    are managed through the API client.
    """
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
    """Create a new user in the database with hashed password for UI authentication."""
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
    """Check if an email address already exists in the user database."""
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


# === Geometry Learning Data Access ===
# 
# Note: Geometry learning operations (questions, theorems, sessions) are now 
# handled through the API client. Use api_client.py for:
# 
# - Questions: api_client.get_first_question(), get_next_question()
# - Answers: api_client.submit_answer()
# - Theorems: api_client.get_all_theorems(), get_relevant_theorems()
# - Sessions: api_client.start_session(), end_session()
# - Statistics: api_client.get_session_statistics()
# 
# The functions below are kept for compatibility but should be migrated
# to use the API client for new development.


# 🔹 בדיקה שה-hash עובד
pw = "סיסמה_שלך_לבדיקה"
hash_pw = hash_password(pw)
print("Generated hash:", hash_pw)
print("Check:", bcrypt.check_password_hash(hash_pw, pw))  # חייב להחזיר True
