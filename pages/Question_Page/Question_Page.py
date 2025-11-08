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
import time
import logging

# Configure detailed logging with timestamps
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

def log_timing(operation_name: str):
    """Decorator to log operation timing."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            logger.info(f"⏱️  START: {operation_name}")
            try:
                result = func(*args, **kwargs)
                elapsed = (time.time() - start_time) * 1000
                logger.info(f"✅ DONE: {operation_name} - {elapsed:.2f}ms")
                return result
            except Exception as e:
                elapsed = (time.time() - start_time) * 1000
                logger.error(f"❌ FAILED: {operation_name} - {elapsed:.2f}ms - {str(e)}")
                raise
        return wrapper
    return decorator

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
    Uses local Flask session tracking to minimize API calls."""
    start_time = time.time()
    logger.info("⏱️  START: check_active_session middleware")
    
    # Check if we already have a session flag in Flask session
    # This avoids unnecessary API calls on every request
    if session.get('api_session_active'):
        elapsed = (time.time() - start_time) * 1000
        logger.info(f"   - Session cached locally (no API call needed)")
        logger.info(f"✅ DONE: check_active_session - {elapsed:.2f}ms")
        return
    
    # Only make API call if we don't have local session flag
    try:
        start_session_time = time.time()
        # Optimistic approach: just start session
        # API should be idempotent (won't create duplicate if exists)
        api_client.start_session()
        start_elapsed = (time.time() - start_session_time) * 1000
        logger.info(f"   - start_session: {start_elapsed:.2f}ms")
        
        # Mark session as active in Flask session
        session['api_session_active'] = True
        session.modified = True
        
    except Exception as e:
        logger.error(f"   - Failed to start API session: {str(e)}")
        # Don't block the request, let individual routes handle errors
    
    total_elapsed = (time.time() - start_time) * 1000
    logger.info(f"✅ DONE: check_active_session - {total_elapsed:.2f}ms")


@question_page.route('/')
def question():
    """Render main question interface."""
    start_time = time.time()
    logger.info("🚀 START: question() route")
    
    user = session.get('user', None)
    user_role = user.get('role', 'user') if user else 'user'
    is_logged_in = user is not None

    if not is_logged_in:
        logger.info("   - User not logged in, redirecting")
        return redirect(url_for('login_page.login'))

    try:
        # Session already ensured by check_active_session middleware
        # No need to start a new session here - this was a performance bottleneck!
        logger.info("   - Session already active (via middleware)")
        
        UserLogger.log_session_start("NEW_SESSION")

        # Get first question from API
        question_start_time = time.time()
        question_data = api_client.get_first_question()
        question_elapsed = (time.time() - question_start_time) * 1000
        logger.info(f"   - get_first_question: {question_elapsed:.2f}ms")
        
        question_id = question_data.get('question_id')
        question_text = question_data.get('question_text')

        # For admin users, get debug information (if available via API)
        debug_info = None
        if user_role == 'admin':
            try:
                debug_start_time = time.time()
                # Try to get session status for debug info
                status = api_client.get_session_status()
                debug_elapsed = (time.time() - debug_start_time) * 1000
                logger.info(f"   - get_session_status (debug): {debug_elapsed:.2f}ms")
                debug_info = status.get('state', {})
            except Exception:
                debug_info = None

        # Get answer options from API
        answers_start_time = time.time()
        answer_options = api_client.get_answer_options()
        answers_elapsed = (time.time() - answers_start_time) * 1000
        logger.info(f"   - get_answer_options: {answers_elapsed:.2f}ms")
        
        answers = answer_options.get('answers', [])

        # Render template
        render_start_time = time.time()
        result = render_template(
            'Question_Page.html',
            user_role=user_role,
            question_id=question_id,
            question_text=question_text,
            debug_info=debug_info,
            answer_options=answers,
            initial_theorems=[]  # Will be populated after first answer
        )
        render_elapsed = (time.time() - render_start_time) * 1000
        logger.info(f"   - render_template: {render_elapsed:.2f}ms")
        
        total_elapsed = (time.time() - start_time) * 1000
        logger.info(f"✅ DONE: question() route - TOTAL: {total_elapsed:.2f}ms")
        return result
        
    except Exception as e:
        total_elapsed = (time.time() - start_time) * 1000
        logger.error(f"❌ FAILED: question() route - {total_elapsed:.2f}ms - {str(e)}")
        return redirect(url_for('login_page.login'))


@question_page.route('/answer', methods=['POST'])
def process_answer():
    """Process user's answer to current question using the API."""
    start_time = time.time()
    logger.info("🚀 START: process_answer() route")
    
    data = request.get_json()
    question_id = data.get('question_id')
    answer = data.get('answer')

    try:
        # Convert answer text to answer_id if necessary
        convert_start = time.time()
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
        convert_elapsed = (time.time() - convert_start) * 1000
        logger.info(f"   - answer mapping: {convert_elapsed:.2f}ms")

        # Submit answer to API
        submit_start = time.time()
        answer_result = api_client.submit_answer(question_id, answer_id)
        submit_elapsed = (time.time() - submit_start) * 1000
        logger.info(f"   - submit_answer API: {submit_elapsed:.2f}ms")
        
        UserLogger.log_question_answer(question_id, f"Answer ID: {answer_id}", answer)

        # Get next question from API
        next_q_start = time.time()
        try:
            next_question_data = api_client.get_next_question()
            next_question_id = next_question_data.get('question_id')
            next_question_text = next_question_data.get('question_text')
            next_q_elapsed = (time.time() - next_q_start) * 1000
            logger.info(f"   - get_next_question API: {next_q_elapsed:.2f}ms")
        except Exception:
            # If no more questions available, end session
            next_question_id = None
            next_question_text = None
            logger.info(f"   - No more questions available")

        # Get relevant theorems from answer submission result
        theorem_start = time.time()
        relevant_theorems = answer_result.get('relevant_theorems', [])
        
        # Format theorems for response
        formatted_theorems = [{
            'id': theorem.get('theorem_id'),
            'text': theorem.get('theorem_text'),
            'weight': theorem.get('weight', 0),
            'category': theorem.get('category', 0),
            'combined_score': theorem.get('combined_score', 0)
        } for theorem in relevant_theorems]
        theorem_elapsed = (time.time() - theorem_start) * 1000
        logger.info(f"   - theorem formatting: {theorem_elapsed:.2f}ms ({len(formatted_theorems)} theorems)")

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

        # Add debug info for admin users
        if session.get('user', {}).get('role') == 'admin':
            try:
                debug_start = time.time()
                status = api_client.get_session_status()
                response_data['debug'] = status.get('state', {})
                debug_elapsed = (time.time() - debug_start) * 1000
                logger.info(f"   - admin debug info: {debug_elapsed:.2f}ms")
            except Exception:
                pass

        total_elapsed = (time.time() - start_time) * 1000
        logger.info(f"✅ DONE: process_answer() - TOTAL: {total_elapsed:.2f}ms")
        
        return jsonify(response_data)

    except Exception as e:
        total_elapsed = (time.time() - start_time) * 1000
        logger.error(f"❌ FAILED: process_answer() - {total_elapsed:.2f}ms - {str(e)}")
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
            # Clear the session flag
            session.pop('api_session_active', None)
            session.modified = True
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
            # Clear the session flag
            session.pop('api_session_active', None)
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