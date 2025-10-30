"""
Question_Page.py
--------------
Description:
    Core controller for the question interface of the Geometric Learning System.
    Manages question presentation, answer processing, session handling, and
    provides real-time feedback through dynamic theorem suggestions.

Routes:
    - /: Main question interface
    - /answer: Process question answers
    - /finish: Handle session completion
    - /cleanup: Clean session data
    - /check-timeout: Verify session timeout status

Author: Karin Hershko and Afik Dadon
Date: February 2025
"""

from flask import Blueprint, render_template, session, jsonify, request, redirect, url_for
from pages.Question_Page.Geometry_Manager import Geometry_Manager
from UserLogger import UserLogger

# Blueprint Configuration
question_page = Blueprint(
    'question_page',
    __name__,
    template_folder='templates',
    static_folder='static'
)


@question_page.before_request
def check_active_session():
    """Middleware to ensure session state is initialized.
    Resets session if no geometry state exists."""
    if 'geometry_state' not in session:
        manager = Geometry_Manager()
        manager.reset_session()


@question_page.route('/')
def question():
    """Render main question interface."""
    user = session.get('user', None)
    user_role = user.get('role', 'user') if user else 'user'
    is_logged_in = user is not None

    if not is_logged_in:
        return redirect(url_for('login_page.login'))

    try:
        manager = Geometry_Manager()
        manager.reset_session()
        UserLogger.log_session_start("NEW_SESSION")

        question_id, question_text, debug_info = manager.get_next_question(
            is_admin=(user_role == 'admin')
        )
        initial_theorems = manager.get_relevant_theorems()

        return render_template(
            'Question_Page.html',
            user_role=user_role,
            question_id=question_id,
            question_text=question_text,
            debug_info=debug_info,
            initial_theorems=initial_theorems
        )
    except Exception as e:
        print(f"Error in question route: {str(e)}")
        return redirect(url_for('login_page.login'))


@question_page.route('/answer', methods=['POST'])
def process_answer():
    """ Process user's answer to current question."""
    data = request.get_json()
    question_id = data.get('question_id')
    answer = data.get('answer')

    try:
        manager = Geometry_Manager()
        manager.process_answer(question_id, answer)

        next_question_id, next_question_text, debug_info = manager.get_next_question(
            is_admin=(session.get('user', {}).get('role') == 'admin')
        )

        questions_history = manager.get_questions_history()
        UserLogger.log_question_answer(question_id, next_question_text, answer)

        # Format theorems for response
        theorems = manager.get_relevant_theorems()
        formatted_theorems = [{
            'id': theorem[0],
            'text': theorem[1],
            'weight': theorem[2],
            'category': theorem[0] if len(theorem) < 4 else theorem[3]
        } for theorem in theorems]

        response_data = {
            'success': True,
            'nextQuestion': {
                'id': next_question_id,
                'text': next_question_text
            },
            'questionsHistory': questions_history,
            'theorems': formatted_theorems,
            'triangle_weights': session['geometry_state']['triangle_weights']
        }

        # Add debug info for admin users
        if session.get('user', {}).get('role') == 'admin':
            response_data['debug'] = debug_info

        return jsonify(response_data)

    except Exception as e:
        print(f"Error in answer route: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@question_page.route('/finish', methods=['POST'])
def finish_session():
    """Handle session completion and cleanup. """
    try:
        data = request.get_json()
        status = data.get('status', 'unknown')

        user = session.get('user')
        if not user:
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401

        UserLogger.log_session_end(status, None)
        session.pop('geometry_state', None)

        redirect_url = (url_for('question_page.question')
                        if status == 'partial'
                        else url_for('home_page.home'))

        return jsonify({
            'success': True,
            'redirect': redirect_url
        })
    except Exception as e:
        print(f"Error in finish_session: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@question_page.route('/cleanup', methods=['POST'])
def cleanup_session():
    """Clean up session data while preserving authentication."""
    try:
        user_data = session.get('user')

        # Get final theorem before cleanup
        manager = Geometry_Manager()
        theorems = manager.get_relevant_theorems()
        final_theorem_id = theorems[0][0] if theorems else None

        # Clear session data except user authentication
        for key in list(session.keys()):
            if key != 'user':
                session.pop(key, None)

        if user_data:
            session['user'] = user_data
            session.modified = True

        UserLogger.log_session_end("CLEANUP", final_theorem_id)
        return jsonify({'success': True})

    except Exception as e:
        print(f"Error in cleanup_session: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@question_page.route('/check-timeout', methods=['GET'])
def check_timeout():
    """ Check if current session has timed out. """
    try:
        manager = Geometry_Manager()
        is_timeout = manager.check_timeout()
        return jsonify({'timeout': is_timeout})
    except Exception as e:
        print(f"Error in check_timeout route: {str(e)}")
        return jsonify({'timeout': False, 'error': str(e)}), 500