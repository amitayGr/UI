"""
Login_Page.py
------------
Description:
    Authentication module for the Geometric Learning System that handles user login,
    logout, and password management functionalities. This module provides secure user
    authentication, password reset capabilities, and session management.

Routes:
    - /: Main login page and authentication
    - /logout: User logout and session cleanup
    - /forgot-password: Password recovery initiation
    - /reset-password/<token>: Password reset with token verification

Author: Karin Hershko and Afik Dadon
Date: February 2025
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from db_utils import verify_user, get_db_connection, hash_password, update_last_login
from UserLogger import UserLogger
from email_utils import EmailUtils
from datetime import datetime

# Blueprint Configuration
login_page = Blueprint(
    'login_page',
    __name__,
    template_folder='templates',
    static_folder='static'
)


@login_page.route('/', methods=['GET', 'POST'])
def login():
    """Handle user login requests and authentication."""
    if request.method == 'POST':
        try:
            email = request.form.get('email')
            password = request.form.get('password')

            # Validate required fields
            if not all([email, password]):
                return jsonify({
                    'success': False,
                    'error': 'נא למלא את כל השדות'
                })

            # Authenticate user
            user = verify_user(email, password)
            if user:
                session['user'] = user
                update_last_login(user['user_id'])
                UserLogger.log_login(True, email)
                return jsonify({'success': True})

            # Log failed attempt and return error
            UserLogger.log_login(False, email, 'Invalid credentials')
            return jsonify({
                'success': False,
                'error': 'אימייל או סיסמה שגויים'
            })

        except Exception as e:
            # Log error and return server error response
            print(f"Login error: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'אירעה שגיאה בעת ההתחברות. אנא נסה שנית מאוחר יותר'
            }), 500

    return render_template('Login_Page.html')


@login_page.route('/logout')
def logout():
    """Handle user logout requests."""
    UserLogger.log_logout()
    session.pop('user', None)
    return redirect(url_for('home_page.home'))


@login_page.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Handle forgotten password requests."""
    if request.method == 'POST':
        email = request.form.get('email')

        if not email:
            return jsonify({
                'success': False,
                'error': 'נא להזין כתובת אימייל'
            })

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Verify email exists
            cursor.execute('SELECT user_id FROM Users WHERE email = ?', (email,))
            user = cursor.fetchone()

            if not user:
                return jsonify({
                    'success': False,
                    'error': 'לא נמצא משתמש עם כתובת האימייל הזו'
                })

            # Setup password reset
            reset_token = EmailUtils.generate_reset_token()
            token_expiry = EmailUtils.get_token_expiry()

            # Update user record
            cursor.execute('''
                UPDATE Users 
                SET reset_token = ?, reset_token_expiry = ?
                WHERE email = ?
            ''', (reset_token, token_expiry, email))
            conn.commit()

            # Send reset instructions
            if EmailUtils.send_reset_email(email, reset_token):
                return jsonify({'success': True})

            return jsonify({
                'success': False,
                'error': 'אירעה שגיאה בשליחת האימייל'
            })

        except Exception as e:
            print(f"Password reset error: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'אירעה שגיאה. אנא נסה שנית מאוחר יותר'
            }), 500
        finally:
            cursor.close()
            conn.close()

    return render_template('forgot_password.html')


@login_page.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Handle password reset requests with verification token."""
    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        # Validate input
        if not all([new_password, confirm_password]):
            return jsonify({
                'success': False,
                'error': 'נא למלא את כל השדות'
            })

        if new_password != confirm_password:
            return jsonify({
                'success': False,
                'error': 'הסיסמאות אינן תואמות'
            })

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Verify token validity
            cursor.execute('''
                SELECT user_id 
                FROM Users 
                WHERE reset_token = ? AND reset_token_expiry > ?
            ''', (token, datetime.now()))
            user = cursor.fetchone()

            if not user:
                return jsonify({
                    'success': False,
                    'error': 'הקישור לאיפוס הסיסמה אינו תקף או שפג תוקפו'
                })

            # Update password
            password_hash = hash_password(new_password)
            cursor.execute('''
                UPDATE Users 
                SET password_hash = ?, reset_token = NULL, reset_token_expiry = NULL
                WHERE user_id = ?
            ''', (password_hash, user[0]))
            conn.commit()

            return jsonify({'success': True})

        except Exception as e:
            print(f"Password reset error: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'אירעה שגיאה. אנא נסה שנית מאוחר יותר'
            }), 500
        finally:
            cursor.close()
            conn.close()

    return render_template('reset_password.html', token=token)