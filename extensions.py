"""
extensions.py
------------
Description:
    Flask extensions initialization for the Geometric Learning System.
    This module initializes Flask extensions that are used across the application,
    particularly for security features like password hashing.

Current Extensions:
    - Flask-Bcrypt: Handles password hashing and verification for user authentication

Usage:
    This extension is used in:
    1. app.py - for initializing bcrypt with the Flask application
    2. db_utils.py - for password hashing and verification functions

Author: Karin Hershko and Afik Dadon
Date: February 2025
"""

from flask_bcrypt import Bcrypt

# Initialize Bcrypt extension
bcrypt = Bcrypt()