"""
UserLogger.py
------------
Description:
    User activity logging system for the Geometric Learning System. This module handles
    all user action logging, providing a comprehensive audit trail of user interactions
    within the application.

Main Components:
    - Action Logging: General-purpose logging mechanism
    - Authentication Logging: Login, registration, and logout events
    - Session Logging: Start and end of learning sessions
    - Activity Logging: Question answers, profile views, and feedback submissions

Database:
    - Table: UserLogs
    - Fields: user_id, action_type, action_data, timestamp (auto-generated)

Author: Karin Hershko and Afik Dadon
Date: February 2025
"""

import json
from datetime import datetime
from flask import session
from db_utils import get_db_connection
from typing import Optional, Dict, Any, Union


class UserLogger:
    """Static class for logging user actions and system events.
    All methods are static as this class serves as a centralized logging interface."""

    @staticmethod
    def log_action(action_type: str, action_data: Union[Dict, str]) -> None:
        """Core logging method that handles all types of log entries."""
        try:
            user_id = session.get('user', {}).get('user_id')

            # Convert action_data to JSON string if it's a dict
            if isinstance(action_data, dict):
                action_data = json.dumps(action_data)

            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO UserLogs (user_id, action_type, action_data)
                    VALUES (?, ?, ?)
                """, (user_id, action_type, action_data))
                conn.commit()

        except Exception as e:
            print(f"Logging error: {str(e)}")
            # Don't raise the exception - logging should never break the main application flow

    @staticmethod
    def log_login(success: bool, email: str, error_message: Optional[str] = None) -> None:
        """Log user login attempts, successful or failed."""
        data = {
            'email': email,
            'success': success,
            'error_message': error_message,
            'timestamp': datetime.now().isoformat()
        }
        UserLogger.log_action('LOGIN_ATTEMPT', data)

    @staticmethod
    def log_registration(success: bool, email: str, error_message: Optional[str] = None) -> None:
        """Log user registration attempts."""
        data = {
            'email': email,
            'success': success,
            'error_message': error_message,
            'timestamp': datetime.now().isoformat()
        }
        UserLogger.log_action('REGISTRATION', data)

    @staticmethod
    def log_question_answer(question_id: int, question_text: str, answer: str) -> None:
        """Log user's answer to a question."""
        data = {
            'question_id': question_id,
            'question_text': question_text,
            'answer': answer,
            'timestamp': datetime.now().isoformat()
        }
        UserLogger.log_action('QUESTION_ANSWER', data)

    @staticmethod
    def log_session_start(session_type: str) -> None:
        """Log the start of a learning session."""
        data = {
            'session_type': session_type,
            'timestamp': datetime.now().isoformat()
        }
        UserLogger.log_action('SESSION_START', data)

    @staticmethod
    def log_session_end(session_type: str, final_theorem_id: Optional[int] = None) -> None:
        """Log the end of a learning session."""
        data = {
            'session_type': session_type,
            'final_theorem_id': final_theorem_id,
            'timestamp': datetime.now().isoformat()
        }
        UserLogger.log_action('SESSION_END', data)

    @staticmethod
    def log_profile_view() -> None:
        """Log when a user views their profile."""
        data = {
            'timestamp': datetime.now().isoformat()
        }
        UserLogger.log_action('PROFILE_VIEW', data)

    @staticmethod
    def log_logout() -> None:
        """Log user logout events."""
        data = {
            'timestamp': datetime.now().isoformat()
        }
        UserLogger.log_action('LOGOUT', data)

    @staticmethod
    def log_feedback_submission() -> None:
        """Log when a user submits feedback."""
        data = {
            "timestamp": datetime.now().isoformat(),
            "action": "FEEDBACK_SUBMISSION"
        }
        UserLogger.log_action('FEEDBACK_SUBMISSION', data)



from flask import Blueprint, render_template, request, redirect
from auth_config import login_user  # כאן אנחנו מייבאים את הפונקציה

login_page = Blueprint('login_page', __name__, template_folder='templates')

@login_page.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        # <<< כאן בדיוק צריך לקרוא ל-login_user >>>
        if login_user(email, password):
            # התחברות נכונה → שמירת session והפניה לדף פרופיל
            return redirect("/profile")
        else:
            # התחברות נכשלת → מציג הודעת שגיאה
            return render_template("login.html", error="Email or password incorrect")

    return render_template("login.html")
