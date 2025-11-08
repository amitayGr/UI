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
    Creates a new API session if one doesn't exist."""
    try:
        # Check if we have an active API session
        api_status = api_client.get_session_status()
        if not api_status.get('active', False):
            # Start a new API session
            api_client.start_session()
    except Exception as e:
        # If API is not available or session creation fails, start a new one
        try:
            api_client.start_session()
        except Exception as start_error:
            print(f"Failed to start API session: {str(start_error)}")
            # Continue with local fallback if needed


@question_page.route('/')
def question():
    """Render main question interface."""
    user = session.get('user', None)
    user_role = user.get('role', 'user') if user else 'user'
    is_logged_in = user is not None

    if not is_logged_in:
        return redirect(url_for('login_page.login'))

    try:
        # Use optimized bootstrap endpoint (auto starts session)
        bootstrap = api_client.bootstrap_initial(
            include_theorems=True,
            include_feedback_options=True,
            include_triangles=True
        )

        if 'error' in bootstrap:
            raise Exception(bootstrap['error'])

        UserLogger.log_session_start(bootstrap.get('session', {}).get('session_id', 'NEW_SESSION'))

        question_data = bootstrap.get('first_question', {})
        question_id = question_data.get('question_id')
        question_text = question_data.get('question_text')
        answers = bootstrap.get('answer_options', {}).get('answers', [])
        theorems = bootstrap.get('theorems', [])

        # Prepare initial theorem list (could be shown as reference/help panel)
        formatted_theorems = [
            {
                'id': t.get('theorem_id'),
                'text': t.get('theorem_text'),
                'category': t.get('category', 0)
            } for t in theorems
        ]

        debug_info = None
        if user_role == 'admin':
            try:
                status = api_client.get_session_status()
                debug_info = status.get('state', {})
            except Exception:
                pass

        return render_template(
            'Question_Page.html',
            user_role=user_role,
            question_id=question_id,
            question_text=question_text,
            debug_info=debug_info,
            answer_options=answers,
            initial_theorems=formatted_theorems
        )
    except Exception as e:
        print(f"Error in question route (bootstrap): {str(e)}")
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

        # Enhanced submit to fetch next question + answer options in same call
        answer_result = api_client.submit_answer_enhanced(
            question_id=question_id,
            answer_id=answer_id,
            include_next_question=True,
            include_answer_options=True
        )

        UserLogger.log_question_answer(question_id, f"Answer ID: {answer_id}", answer)

        next_question = answer_result.get('next_question')
        answer_options = answer_result.get('answer_options', {})
        next_answers = answer_options.get('answers') if answer_options else []

        relevant_theorems = answer_result.get('relevant_theorems', [])
        formatted_theorems = [
            {
                'id': th.get('theorem_id'),
                'text': th.get('theorem_text'),
                'weight': th.get('weight', 0),
                'category': th.get('category', 0),
                'combined_score': th.get('combined_score', 0)
            } for th in relevant_theorems
        ]

        updated_weights = answer_result.get('updated_weights', {})

        response_data = {
            'success': True,
            'nextQuestion': {
                'id': next_question.get('question_id'),
                'text': next_question.get('question_text'),
                'answers': next_answers
            } if next_question else None,
            'theorems': formatted_theorems,
            'triangle_weights': updated_weights
        }

        # Add debug info for admin users
        if session.get('user', {}).get('role') == 'admin':
            try:
                status = api_client.get_session_status()
                response_data['debug'] = status.get('state', {})
            except Exception:
                pass

        return jsonify(response_data)

    except Exception as e:
        print(f"Error in answer route: {str(e)}")
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
    """Check if current session has timed out using API."""
    try:
        # Check API session status
        status = api_client.get_session_status()
        is_active = status.get('active', False)
        
        # If API session is not active, consider it timed out
        return jsonify({'timeout': not is_active})
    except Exception as e:
        print(f"Error in check_timeout route: {str(e)}")
        return jsonify({'timeout': True, 'error': str(e)}), 500