

# auth_config.py
from flask import session
from db_utils import verify_user, update_last_login
from UserLogger import UserLogger

def login_user(email: str, password: str) -> bool:
    """
    מנסה להתחבר עם אימייל וסיסמה.
    מחזיר True אם ההתחברות הצליחה, False אחרת.
    """
    user = verify_user(email, password)

    if user is None:
        # אם הסיסמה או האימייל לא נכונים
        UserLogger.log_login(False, email, "Email or password incorrect")
        return False

    # שמירה ב-session
    session['user'] = {
        'user_id': user['user_id'],
        'email': user['email'],
        'first_name': user['first_name'],
        'last_name': user['last_name'],
        'role': user['role']
    }

    # עדכון last login ב-DB
    update_last_login(user['user_id'])

    # רישום התחברות מוצלחת
    UserLogger.log_login(True, email)
    return True
