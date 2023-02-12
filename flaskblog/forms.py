from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (StringField, PasswordField, SubmitField,
                     BooleanField, IntegerField, FloatField, SelectField)
from wtforms.validators import DataRequired, Length, Email, EqualTo, NumberRange, ValidationError, InputRequired
from flaskblog.models import User


class RegistrationForm(FlaskForm):
    username = StringField('用户名',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('邮箱',
                        validators=[DataRequired(), Email()])
    password = PasswordField('密码', validators=[DataRequired()])
    confirm_password = PasswordField('确认密码',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('注册')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('该用户名已被使用，请更换用户名。')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('该用户名已被使用，请更换邮箱。')


class LoginForm(FlaskForm):
    email = StringField('邮箱',
                        validators=[DataRequired(), Email()])
    password = PasswordField('密码', validators=[DataRequired()])
    remember = BooleanField('自动登录')
    submit = SubmitField('登录')


class Diagnosis(FlaskForm):
    name = StringField('姓名', validators=[DataRequired(), Length(min=2, max=10)])
    age = IntegerField('年龄', validators=[DataRequired(), NumberRange(min=0, max=130)])
    sex = SelectField('性别', choices=[('男', '男'), ('女', '女')], validators=[DataRequired()])
    exposure_year = FloatField('二氧化硅、石棉粉尘暴露时间/年，没有请填“0”',
                               validators=[InputRequired(), NumberRange(min=0, max=50)])
    smoke = FloatField('吸烟史/年，没有请填“0”', validators=[InputRequired(), NumberRange(min=0, max=50)])
    drink = FloatField('酗酒史/年，没有请填“0”', validators=[InputRequired(), NumberRange(min=0, max=50)])
    picture = FileField('您的胸部X光片， 请提交PNG，JPG格式', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    submit = SubmitField('上传')


class RequestResetForm(FlaskForm):
    email = StringField('请输入您的邮箱',
                        validators=[DataRequired(), Email()])
    submit = SubmitField('提交重置密码申请')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError('该邮箱不存在，请先注册。')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('请输入密码', validators=[DataRequired()])
    confirm_password = PasswordField('请确认密码',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('重置密码')
