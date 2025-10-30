"""
Feedback_Page.py
--------------
Description:
    Handles user feedback collection for the Geometric Learning System.
    Manages feedback form display and submission processing.

Author: Karin Hershko and Afik Dadon
Date: February 2025
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from db_utils import get_db_connection
from UserLogger import UserLogger
from typing import Dict, Union
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

feedback_page = Blueprint('feedback_page', __name__,
                          template_folder='templates',
                          static_folder='static')


@feedback_page.route('/')
def feedback() -> Union[str, redirect]:
    """Display the feedback form page.
    Requires user authentication."""
    user = session.get('user', None)
    if not user:
        return redirect(url_for('login_page.login'))
    return render_template('Feedback_Page.html')


@feedback_page.route('/submit', methods=['POST'])
def submit_feedback() -> jsonify:
    """Process feedback form submission.
    Validates input and stores in database."""
    try:
        # Validate user session
        if not _validate_user_session():
            return jsonify({
                'success': False,
                'error': 'User is not logged in'
            }), 401

        # Get and validate form data
        data = request.get_json()
        if not data:
            logger.error("No feedback data received")
            return jsonify({
                'success': False,
                'error': 'No feedback data received'
            }), 400

        # Save feedback to database
        _save_feedback_to_db(data)

        # Log successful submission
        UserLogger.log_feedback_submission()

        return jsonify({'success': True})

    except Exception as e:
        logger.error(f"Error in submit_feedback: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'אירעה שגיאה בשמירת המשוב. אנא נסה שוב או צור קשר עם התמיכה.'
        }), 500


# === Helper Functions ===

def _validate_user_session() -> bool:
    """Validate user session and extract user ID."""
    user = session.get('user')
    if not user:
        logger.warning("No user in session during feedback submission")
        return False

    user_id = user.get('user_id')
    if not user_id:
        logger.warning("No user ID in session")
        return False

    return True


def _save_feedback_to_db(data: Dict) -> None:
    """Save feedback data to database."""
    user_id = session['user']['user_id']

    with get_db_connection() as conn:
        cursor = conn.cursor()

        query = """
            INSERT INTO UserFeedback (
                user_id, 
                usability_easy_to_use, usability_clear_questions,
                usability_clear_interface, usability_easy_navigation,
                educational_concepts, educational_theorems,
                educational_guidance, educational_learning,
                format_dont_know_helpful, format_sufficient_options,
                format_would_use_again,
                intelligence_understood_responses, intelligence_relevant_questions,
                missing_questions, unclear_questions,
                suggested_improvements, expected_questions
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        values = (
            user_id,
            data.get('usability_easy_to_use'),
            data.get('usability_clear_questions'),
            data.get('usability_clear_interface'),
            data.get('usability_easy_navigation'),
            data.get('educational_concepts'),
            data.get('educational_theorems'),
            data.get('educational_guidance'),
            data.get('educational_learning'),
            data.get('format_dont_know_helpful'),
            data.get('format_sufficient_options'),
            data.get('format_would_use_again'),
            data.get('intelligence_understood_responses'),
            data.get('intelligence_relevant_questions'),
            data.get('missing_questions', ''),
            data.get('unclear_questions', ''),
            data.get('suggested_improvements', ''),
            data.get('expected_questions', '')
        )

        cursor.execute(query, values)