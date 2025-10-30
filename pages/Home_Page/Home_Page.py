"""
Home_Page.py
-----------
Description:
    Blueprint handler for the home page of the Geometric Learning System.
    Manages the rendering of the main landing page, handling user session state
    and providing personalized content based on authentication status.

Main Components:
    - Blueprint Registration: Sets up the Flask blueprint for the home page
    - Route Handler: Manages the main '/' route and template rendering
    - Session Management: Handles user session data for personalized content

Author: Karin Hershko and Afik Dadon
Date: February 2025
"""

from flask import Blueprint, render_template, session

# Blueprint Configuration
home_page = Blueprint(
    'home_page',
    __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/Home_Page/static'
)


@home_page.route('/')
def home():
    """Render the home page with personalized content based on user authentication status."""
    # Extract user data from session if available
    user = session.get('user', None)
    user_name = user['first_name'] if user else None
    is_logged_in = user is not None

    return render_template(
        'Home_Page.html',
        user_name=user_name,
        is_logged_in=is_logged_in
    )