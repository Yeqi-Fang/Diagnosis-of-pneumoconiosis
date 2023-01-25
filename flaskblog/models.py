from datetime import datetime
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
# from itsdangerous import URLSafeTimedSerializer as Serializer
from . import db, login_manager, app
from flask_login import UserMixin


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
    # linux


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    # image_file = db.Column(db.String(20), nullable=True, default='default.jpeg')
    password = db.Column(db.String(60), nullable=False)
    xrays = db.relationship('Xray', backref='author', lazy=True)

    def get_reset_token(self, expires_sec=1800):
        s = Serializer(app.config['SECRET_KEY'], expires_sec)
        # Token.
        return s.dumps({'user_id': self.id}).decode('utf-8')

    @staticmethod
    def verify_reset_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        return User.query.get(user_id)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"


class Xray(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    sex = db.Column(db.String(1), nullable=False)
    exposure_year = db.Column(db.Float, nullable=False)
    smoke = db.Column(db.Float, nullable=False)
    PNEUMONIA = db.Column(db.Boolean, nullable=True)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.now)
    pic_address = db.Column(db.String(20), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # advise = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f"Xray('{self.date_posted}')"
