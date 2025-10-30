"""
Contact_Page.py
--------------
Description:
    Handles the contact form functionality for the Geometric Learning System.
    Manages user message submissions and form validation.

Author: Karin Hershko and Afik Dadon
Date: February 2025
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from db_utils import get_db_connection
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

contact_page = Blueprint('contact_page', __name__,
                         template_folder='templates',
                         static_folder='static',
                         static_url_path='/contact/static')

@contact_page.route('/')
def contact() -> str:
    """ Display the contact form page.
    If user is logged in, pre-fill their information."""
    session.pop('_flashes', None)  # Clear any existing flash messages
    user = session.get('user', None)
    return render_template('Contact_Page.html', user=user)


@contact_page.route('/submit', methods=['POST'])
def submit() -> redirect:
    """Process contact form submission.
    Validates input and stores message in database."""
    if request.method != 'POST':
        return redirect(url_for('contact_page.contact'))

    try:
        if not _validate_form_data(request.form):
            flash('כל השדות הם חובה', 'error')
            return redirect(url_for('contact_page.contact'))

        _save_message_to_db(request.form)
        flash('ההודעה נשלחה בהצלחה!', 'success')
        return redirect(url_for('home_page.home'))

    except Exception as e:
        logger.error(f"Error processing contact form: {str(e)}")
        flash('אירעה שגיאה בשליחת ההודעה. אנא נסה שוב.', 'error')
        return redirect(url_for('contact_page.contact'))



# === Helper Functions ===
def _validate_form_data(form_data: dict) -> bool:
    """Validate that all required fields are present and non-empty."""
    required_fields = ['name', 'email', 'subject', 'message']
    return all(form_data.get(field, '').strip() for field in required_fields)


def _save_message_to_db(form_data: dict) -> None:
    """Save contact message to database."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO ContactMessages (name, email, subject, message)
            VALUES (?, ?, ?, ?)
        """, (
            form_data['name'],
            form_data['email'],
            form_data['subject'],
            form_data['message']
        ))
        conn.commit()