import os

import boto3
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail
# from flask_s3 import FlaskS3

# from flask import url_for

app = Flask(__name__)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI')
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
# sqlite:///site.db
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAIL_SERVER'] = 'smtp-mail.outlook.com'  #
app.config['MAIL_PORT'] = 587  # for outlook25
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('EMAIL_USER')
app.config['MAIL_PASSWORD'] = os.environ.get('EMAIL_PASS')
app.config['FLASKS3_BUCKET_NAME'] = 'testing-bucket-flask2'
# app.config['FLASKS3_BUCKET_DOMAIN'] = u's3.ap-northeast-1.amazonaws.com'
# https://testing-bucket-flask2./static/default.jpeg

s3 = boto3.client('s3')
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
mail = Mail(app)
migrate = Migrate(app, db)
# s3 = FlaskS3(app)

login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
from . import routes
