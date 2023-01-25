import os
import json
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail

with open('/etc/config.json') as f:
	config = json.load(f)


app = Flask(__name__)
app.config['SECRET_KEY'] = config.get('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = config.get('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAIL_SERVER'] = 'smtp-mail.outlook.com'  #
app.config['MAIL_PORT'] = 587  # for outlook25
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = config.get('EMAIL_USER')
app.config['MAIL_PASSWORD'] = config.get('EMAIL_PASS')

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
mail = Mail(app)
migrate = Migrate(app, db)

login_manager.login_view = 'login'
login_manager.login_message_category = 'info'



from . import routes
