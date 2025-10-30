"""
User_Profile_Page.py
------------------
Description:
    A Flask Blueprint that handles user profile functionality. This component manages
    user statistics, activity history, and admin-specific analytics. It provides
    different views and data based on user roles.

Main Components:
    - User Statistics: Tracks user engagement and activity
    - Activity History: Shows recent user actions
    - Admin Dashboard: System-wide analytics and management tools
    - Question Analytics: Usage statistics for questions
    - Theorem Database: Management of geometric theorems

Author: Karin Hershko and Afik Dadon
Date: February 2025
"""

from flask import Blueprint, render_template, session, redirect, url_for
from db_utils import get_db_connection

user_profile_page = Blueprint('user_profile_page', __name__,
                              template_folder='templates',
                              static_folder='static')


@user_profile_page.route('/')
def profile():
    """Handle profile page requests. Shows different views based on user role."""
    user = session.get('user')
    if not user:
        return redirect(url_for('login_page.login'))

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            user_stats = _get_user_statistics(cursor, user['user_id'])
            recent_activity = _get_recent_activity(cursor, user) if user['role'] != 'admin' else None
            admin_stats = _get_admin_statistics(cursor) if user['role'] == 'admin' else None

            return render_template('User_Profile_Page.html',
                                   user=user,
                                   user_stats=user_stats,
                                   recent_activity=recent_activity,
                                   admin_stats=admin_stats)

    except Exception as e:
        # Log the error but return a graceful fallback
        print(f"Database error: {str(e)}")
        return _render_fallback_profile(user)


def _get_user_statistics(cursor, user_id):
    """Retrieve user activity statistics."""
    cursor.execute("""
        WITH UserSessions AS (
            SELECT COUNT(*) as total_starts
            FROM UserLogs 
            WHERE user_id = ? AND action_type = 'SESSION_START'
        ),
        CompletedSessions AS (
            SELECT COUNT(*) as total_completed
            FROM UserLogs 
            WHERE user_id = ? AND action_type = 'SESSION_END'
        ),
        LoginAttempts AS (
            SELECT COUNT(*) as login_count
            FROM UserLogs 
            WHERE user_id = ? AND action_type = 'LOGIN_ATTEMPT'
        )
        SELECT 
            ISNULL(UserSessions.total_starts, 0) as total_sessions,
            CASE 
                WHEN ISNULL(CompletedSessions.total_completed, 0) > ISNULL(UserSessions.total_starts, 0) 
                THEN ISNULL(UserSessions.total_starts, 0)
                ELSE ISNULL(CompletedSessions.total_completed, 0)
            END as completed_sessions,
            ISNULL(LoginAttempts.login_count, 0) as login_count
        FROM UserSessions
        CROSS JOIN CompletedSessions
        CROSS JOIN LoginAttempts
    """, (user_id, user_id, user_id))
    return cursor.fetchone()


def _get_recent_activity(cursor, user):
    """Get user's recent activity history."""
    if user['role'] == 'admin':
        return None

    cursor.execute("""
        SELECT TOP 5 timestamp, action_type
        FROM UserLogs
        WHERE user_id = ?
        ORDER BY timestamp DESC
    """, (user['user_id'],))
    return cursor.fetchall()


def _get_admin_statistics(cursor):
    """Get system-wide statistics for admin dashboard."""
    # Get system overview statistics
    cursor.execute("""
        SELECT 
            (SELECT COUNT(*) FROM Users) as total_users,
            (SELECT COUNT(DISTINCT user_id) 
             FROM UserLogs 
             WHERE timestamp >= DATEADD(day, -1, GETDATE())) as active_users_day,
            (SELECT COUNT(DISTINCT user_id) 
             FROM UserLogs 
             WHERE timestamp >= DATEADD(day, -7, GETDATE())) as active_users_week,
            (SELECT COUNT(*) 
             FROM UserLogs 
             WHERE action_type = 'SESSION_END' 
             AND action_data LIKE '%"final_theorem_id"%'
             AND action_data NOT LIKE '%"final_theorem_id": null%') as completed_exercises
    """)
    system_stats = cursor.fetchone()

    # Get question analytics
    cursor.execute("""
        SELECT 
            q.question_id,
            CAST(q.question_text AS VARCHAR(MAX)) as question_text,
            q.difficulty_level,
            COUNT(DISTINCT ul.user_id) as unique_users,
            (SELECT COUNT(*) 
             FROM UserLogs 
             WHERE action_type = 'QUESTION_ANSWER' 
             AND JSON_VALUE(action_data, '$.question_id') = CAST(q.question_id as VARCHAR)) as total_asked
        FROM Questions q
        LEFT JOIN UserLogs ul ON ul.action_type = 'QUESTION_ANSWER' 
            AND JSON_VALUE(ul.action_data, '$.question_id') = CAST(q.question_id as VARCHAR)
        WHERE q.active = 1
        GROUP BY q.question_id, CAST(q.question_text AS VARCHAR(MAX)), q.difficulty_level
        ORDER BY total_asked DESC
    """)
    question_analytics = cursor.fetchall()

    # Get theorems data
    cursor.execute("""
        SELECT t.theorem_id, t.theorem_text, t.category
        FROM Theorems t
        WHERE t.active = 1
        ORDER BY t.theorem_id
    """)
    theorems_data = cursor.fetchall()

    return {
        'system_stats': system_stats,
        'question_analytics': question_analytics,
        'theorems': theorems_data
    }


def _render_fallback_profile(user):
    """Render profile page with fallback data in case of errors."""
    return render_template('User_Profile_Page.html',
                           user=user,
                           user_stats=(0, 0, 0),
                           recent_activity=None,
                           admin_stats={'system_stats': (0, 0, 0, 0),
                                        'theorems': [],
                                        'question_analytics': []} if user['role'] == 'admin' else None)