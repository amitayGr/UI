"""
Question_Page.py
--------------
Description:
    Core controller for the question interface of the Geometric Learning System.
    Manages question presentation, answer processing, session handling, and
    provides real-time feedback through dynamic theorem suggestions.
    
    Updated to use the centralized API client for localhost:17654 communication.

Routes:
    - /: Main question interface
    - /answer: Process question answers
    - /finish: Handle session completion
    - /cleanup: Clean session data
    - /check-timeout: Verify session timeout status

Author: Karin Hershko and Afik Dadon
Date: February 2025
Updated: November 2025 - API Integration
"""

from flask import Blueprint, render_template, session, jsonify, request, redirect, url_for
from api_client import api_client
from UserLogger import UserLogger

# Blueprint Configuration
question_page = Blueprint(
    'question_page',
    __name__,
    template_folder='templates',
    static_folder='static'
)


@question_page.after_request
def after_request(response):
    """Clean up API client session after each request."""
    # This ensures thread-local sessions are properly cleaned up
    # helping to prevent SQLite threading issues
    return response


@question_page.before_request
def check_active_session():
    """Middleware to ensure API session state is initialized.
    Creates a new API session if one doesn't exist.
    
    OPTIMIZATION: Only checks session status when flag is not set,
    reducing redundant calls while ensuring session validity.
    """
    try:
        # If we don't have a local flag, check with API
        if not session.get('api_session_active', False):
            # Verify with API if session is actually active
            try:
                api_status = api_client.get_session_status()
                if api_status.get('active', False):
                    # Session exists, set flag
                    session['api_session_active'] = True
                else:
                    # No active session, start one
                    api_client.start_session()
                    session['api_session_active'] = True
            except Exception:
                # API call failed or no session, start a new one
                api_client.start_session()
                session['api_session_active'] = True
    except Exception as e:
        print(f"Failed to ensure API session: {str(e)}")
        session['api_session_active'] = False


@question_page.route('/')
def question():
    """Render main question interface."""
    user = session.get('user', None)
    user_role = user.get('role', 'user') if user else 'user'
    is_logged_in = user is not None

    if not is_logged_in:
        return redirect(url_for('login_page.login'))

    try:
        # Middleware already ensures we have a session
        UserLogger.log_session_start("NEW_SESSION")

        # Get first question from API
        question_data = api_client.get_first_question()
        question_id = question_data.get('question_id')
        question_text = question_data.get('question_text')

        # For admin users, skip debug info to avoid extra API call
        debug_info = None

        # Get answer options from API
        answer_options = api_client.get_answer_options()
        answers = answer_options.get('answers', [])

        return render_template(
            'Question_Page.html',
            user_role=user_role,
            question_id=question_id,
            question_text=question_text,
            debug_info=debug_info,
            answer_options=answers,
            initial_theorems=[]  # Will be populated after first answer
        )
    except Exception as e:
        print(f"Error in question route: {str(e)}")
        # If we get a session error, clear the flag so middleware will recreate
        if "session" in str(e).lower():
            session['api_session_active'] = False
        return redirect(url_for('login_page.login'))


@question_page.route('/answer', methods=['POST'])
def process_answer():
    """Process user's answer to current question using the API."""
    data = request.get_json()
    question_id = data.get('question_id')
    answer = data.get('answer')

    try:
        # Convert answer text to answer_id if necessary
        # The API expects answer_id (0-3), but UI might send text
        answer_id = answer
        if isinstance(answer, str):
            # Map answer text to ID based on API documentation
            answer_mapping = {
                'לא': 0,
                'כן': 1, 
                'לא יודע': 2,
                'כנראה': 3
            }
            answer_id = answer_mapping.get(answer, 2)  # Default to "לא יודע"

        # Submit answer to API
        answer_result = api_client.submit_answer(question_id, answer_id)
        
        UserLogger.log_question_answer(question_id, f"Answer ID: {answer_id}", answer)

        # Get next question from API
        try:
            next_question_data = api_client.get_next_question()
            next_question_id = next_question_data.get('question_id')
            next_question_text = next_question_data.get('question_text')
        except Exception:
            # If no more questions available, end session
            next_question_id = None
            next_question_text = None

        # Get relevant theorems from answer submission result
        relevant_theorems = answer_result.get('relevant_theorems', [])
        
        # Format theorems for response
        formatted_theorems = [{
            'id': theorem.get('theorem_id'),
            'text': theorem.get('theorem_text'),
            'weight': theorem.get('weight', 0),
            'category': theorem.get('category', 0),
            'combined_score': theorem.get('combined_score', 0)
        } for theorem in relevant_theorems]

        # Get updated weights from answer result
        updated_weights = answer_result.get('updated_weights', {})

        response_data = {
            'success': True,
            'nextQuestion': {
                'id': next_question_id,
                'text': next_question_text
            } if next_question_id else None,
            'theorems': formatted_theorems,
            'triangle_weights': updated_weights
        }

        # OPTIMIZATION: Removed debug info API call for admin users
        # This saves 50-100ms on every answer submission
        # The session state is maintained by the API via cookies

        return jsonify(response_data)

    except Exception as e:
        print(f"Error in answer route: {str(e)}")
        # If we get a session error, clear the flag so middleware will recreate
        if "session" in str(e).lower():
            session['api_session_active'] = False
        return jsonify({'success': False, 'error': str(e)}), 500


@question_page.route('/finish', methods=['POST'])
def finish_session():
    """Handle session completion and cleanup using the API."""
    try:
        data = request.get_json()
        status = data.get('status', 'unknown')
        feedback_id = data.get('feedback_id')  # Optional feedback
        triangle_types = data.get('triangle_types')  # Optional
        helpful_theorems = data.get('helpful_theorems')  # Optional

        user = session.get('user')
        if not user:
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401

        # End the API session with optional feedback
        try:
            api_client.end_session(
                feedback=feedback_id,
                triangle_types=triangle_types,
                helpful_theorems=helpful_theorems,
                save_to_db=True
            )
            # Clear the session active flag
            session['api_session_active'] = False
        except Exception as api_error:
            print(f"API session end failed: {str(api_error)}")
            # Continue with local cleanup

        UserLogger.log_session_end(status, None)

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

        # End the API session if active
        try:
            api_client.end_session(save_to_db=False)  # Don't save on cleanup
            # Clear the session active flag
            session['api_session_active'] = False
        except Exception as api_error:
            print(f"API cleanup failed: {str(api_error)}")
            # Continue with local cleanup

        # Clear local Flask session data except user authentication
        for key in list(session.keys()):
            if key != 'user':
                session.pop(key, None)

        if user_data:
            session['user'] = user_data
            session.modified = True

        UserLogger.log_session_end("CLEANUP", None)
        return jsonify({'success': True})

    except Exception as e:
        print(f"Error in cleanup_session: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@question_page.route('/check-timeout', methods=['GET'])
def check_timeout():
    """Check if current session has timed out.
    
    Uses the local flag first, but if flag indicates active session,
    we trust it since middleware validates on each request.
    """
    try:
        # Check local Flask session flag
        # Middleware ensures this is kept in sync with API
        is_active = session.get('api_session_active', False)
        return jsonify({'timeout': not is_active})
    except Exception as e:
        print(f"Error in check_timeout route: {str(e)}")
        return jsonify({'timeout': True, 'error': str(e)}), 500