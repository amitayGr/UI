"""
Registration_Page.py
------------------
Description:
    A Flask Blueprint that handles user registration functionality. This component manages
    user registration with input validation, password hashing, and error handling.
    It includes both server-side validation and client-side feedback mechanisms.

Main Components:
    - Input Validation: Validates user input for names, email, and password
    - User Creation: Handles secure user creation with password hashing
    - Error Handling: Comprehensive error handling with user-friendly messages
    - Response Management: JSON responses for AJAX requests

Author: Karin Hershko and Afik Dadon
Date: February 2025
"""

from flask import Blueprint, render_template, request, jsonify
from db_utils import create_user, hash_password
from UserLogger import UserLogger
import re

registration_page = Blueprint('registration_page', __name__,
                              template_folder='templates',
                              static_folder='static')


class InputValidator:
    """Handles validation of user input for registration."""
    @staticmethod
    def validate_name(name: str, field_name: str) -> tuple[bool, str | None]:
        """Validate a name field (first name or last name). """
        name_pattern = r'^[\u0590-\u05FFa-zA-Z\s]+$'
        if not re.match(name_pattern, name):
            return False, f'{field_name} חייב להכיל אותיות בלבד'
        return True, None

    @staticmethod
    def validate_email(email: str) -> tuple[bool, str | None]:
        """ Validate email format. """
        email_pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        if not re.match(email_pattern, email):
            return False, 'כתובת אימייל לא תקינה'
        return True, None

    @staticmethod
    def validate_password(password: str) -> tuple[bool, str | None]:
        """Validate password strength."""
        if len(password) < 8:
            return False, 'הסיסמה חייבת להכיל לפחות 8 תווים'
        if not re.search(r'[A-Z]', password):
            return False, 'הסיסמה חייבת להכיל לפחות אות גדולה אחת'
        if not re.search(r'[a-z]', password):
            return False, 'הסיסמה חייבת להכיל לפחות אות קטנה אחת'
        if not re.search(r'\d', password):
            return False, 'הסיסמה חייבת להכיל לפחות ספרה אחת'
        return True, None


def validate_registration_input(first_name: str, last_name: str,
                                email: str, password: str) -> tuple[bool, str | None]:
    """Validate all registration input fields."""
    validator = InputValidator()

    # Validate first name
    valid, error = validator.validate_name(first_name, 'שם פרטי')
    if not valid:
        return False, error

    # Validate last name
    valid, error = validator.validate_name(last_name, 'שם משפחה')
    if not valid:
        return False, error

    # Validate email
    valid, error = validator.validate_email(email)
    if not valid:
        return False, error

    # Validate password
    valid, error = validator.validate_password(password)
    if not valid:
        return False, error

    return True, None


@registration_page.route('/', methods=['GET', 'POST'])
def register():
    """Handle GET and POST requests for user registration."""
    if request.method == 'POST':
        try:
            # Extract form data
            first_name = request.form.get('first_name')
            last_name = request.form.get('last_name')
            email = request.form.get('email')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')

            # Validate required fields
            if not all([first_name, last_name, email, password, confirm_password]):
                return jsonify({
                    'success': False,
                    'error': 'נא למלא את כל השדות'
                })

            # Validate password confirmation
            if password != confirm_password:
                return jsonify({
                    'success': False,
                    'error': 'הסיסמאות אינן תואמות'
                })

            # Validate input fields
            is_valid, error_message = validate_registration_input(
                first_name, last_name, email, password
            )
            if not is_valid:
                return jsonify({
                    'success': False,
                    'error': error_message
                })

            # Hash password and create user
            hashed_password = hash_password(password)
            if create_user(first_name, last_name, email, hashed_password):
                UserLogger.log_registration(True, email)
                return jsonify({'success': True})
            else:
                UserLogger.log_registration(False, email, 'Email already exists')
                return jsonify({
                    'success': False,
                    'error': 'כתובת האימייל שהזנת כבר קיימת במערכת'
                })

        except Exception as e:
            UserLogger.log_registration(False, email, str(e))
            return jsonify({
                'success': False,
                'error': 'אירעה שגיאה בעת יצירת המשתמש. אנא נסה שנית מאוחר יותר'
            }), 500

    return render_template('Registration_Page.html')