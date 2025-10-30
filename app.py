# app.py
from flask import Flask
from flask_session import Session
from extensions import bcrypt
import os
from datetime import timedelta

app = Flask(__name__)

app.secret_key = "somesecret"

# Configure app first
app.config.update(
    JSON_AS_ASCII=False,
    SECRET_KEY=os.environ.get('SECRET_KEY', 'default-secret-key'),
    SESSION_TYPE='filesystem',
    SESSION_PERMANENT=True,
    PERMANENT_SESSION_LIFETIME=timedelta(hours=5),  # Session will last 5 hours
    SESSION_FILE_THRESHOLD=500  # Maximum number of session files stored
)

# Initialize extensions
bcrypt.init_app(app)
Session(app)

from pages.Home_Page.Home_Page import home_page
app.register_blueprint(home_page, url_prefix='/')

from pages.Registration_Page.Registration_Page import registration_page
app.register_blueprint(registration_page, url_prefix='/register')

from pages.Login_Page.Login_Page import login_page
app.register_blueprint(login_page, url_prefix='/login')

from pages.User_Profile_Page.User_Profile_Page import user_profile_page
app.register_blueprint(user_profile_page, url_prefix='/profile')

from pages.Question_Page.Question_Page import question_page
app.register_blueprint(question_page, url_prefix='/question')

from pages.Feedback_Page.Feedback_Page import feedback_page
app.register_blueprint(feedback_page, url_prefix='/feedback')

from pages.Contact_Page.Contact_Page import contact_page
app.register_blueprint(contact_page, url_prefix='/contact')



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))