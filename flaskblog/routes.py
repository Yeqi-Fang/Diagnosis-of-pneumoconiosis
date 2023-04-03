import builtins
import os
import random
import secrets
import boto3
import numpy as np
from PIL import Image
from botocore.exceptions import ClientError
from flask import render_template, url_for, flash, redirect, request, session
# from flask_s3 import url_for
from . import app, db, bcrypt, mail
from flaskblog.forms import RegistrationForm, LoginForm, Diagnosis, RequestResetForm, ResetPasswordForm
from flaskblog.models import User, Xray
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message
from tensorflow.keras import regularizers, initializers
from tensorflow.keras.applications import EfficientNetB0
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Flatten, GlobalAveragePooling2D, Dropout, BatchNormalization

# if platform == 'linux':
#     subprocess.run(['cp', '-r', 'flaskblog/.aws', '~/.aws'])
#     subprocess.run(['ls', '~/.aws'])
#
# print('OS')
# print(platform + '\n\n\n')

os.environ['AWS_DEFAULT_REGION'] = "ap-northeast-1"
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
bucketname = 'testing-bucket-flask2'
RegL = 0.0
SIZE = 750
EPOCHS = 100
DROPOUT_RATE = 0.55
INPUT_SHAPE = (SIZE, SIZE, 3)

conv_base = EfficientNetB0(input_shape=(SIZE, SIZE, 3), weights='imagenet', include_top=False)
model = Sequential()
model.add(conv_base)
model.add(GlobalAveragePooling2D())
model.add(Dense(1024, activation='relu', kernel_regularizer=regularizers.l2(RegL),
                kernel_initializer=initializers.TruncatedNormal(mean=0.0, stddev=0.05)
                ))
model.add(Dropout(DROPOUT_RATE))
model.add(Dense(128, activation='relu', kernel_regularizer=regularizers.l2(RegL),
                kernel_initializer=initializers.TruncatedNormal(mean=0.0, stddev=0.05)
                ))
model.add(Dropout(DROPOUT_RATE))
model.add(Dense(32, activation='relu', kernel_regularizer=regularizers.l2(RegL),
                kernel_initializer=initializers.TruncatedNormal(mean=0.0, stddev=0.05)
                ))
model.add(Dropout(DROPOUT_RATE))
model.add(Dense(1, activation='sigmoid'))
# model.compile(optimizer=optimizers.Adam(lr=LEARNING_RATE),
#               loss='binary_crossentropy', metrics=['mae']
#               )
model.load_weights("flaskblog/epoch_87-val_mae_0.097.hdf5")

s3 = boto3.client('s3',
                  aws_access_key_id=os.environ.get('aws_access_key_id'),
                  aws_secret_access_key=os.environ.get('aws_secret_access_key'))


@app.route("/home")
def home():
    # posts = Post.query.all()
    # print(url_for('static', filename='test'))
    # print('fa')
    return render_template('home.html')


@app.route("/about")
def about():
    return render_template('about.html', title='About')


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('成功创建账号，请登录', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('登陆失败，请检查账号和密码', 'danger')
    return render_template('login.html', title='Login', form=form)


@login_required
@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('diagnosis'))


def upload_file(file_name, bucket, object_name=None):
    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = os.path.basename(file_name)

    try:
        response = s3.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        print(e)
        return False
    return True


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)
    print(picture_path)
    # picture_path = url_for('static', filename='profile_pics/' + picture_fn)
    # print(picture_path)
    i = Image.open(form_picture)
    i.save(picture_path)
    upload_file(picture_path, 'testing-bucket-flask2', f'static/profile_pics/{picture_fn}')
    print(os.environ.get('aws_access_key_id'))
    return picture_fn


def open_path(filepath, bucketname):
    if not os.path.exists(filepath):
        file_name = os.path.basename(filepath)
        with open(filepath, 'wb') as f:
            s3.download_fileobj(bucketname, 'static/profile_pics/' + file_name, f)


def divide(y):
    i, j, k = .6, 1.8, 2.45
    if y < i:
        x = 0
    elif i <= y < j:
        x = 1
    elif j <= y < k:
        x = 2
    else:
        x = 3
    return x


@app.route('/', methods=['GET', 'POST'])
@app.route("/diagnosis", methods=['GET', 'POST'])
@login_required
def diagnosis():
    form = Diagnosis()
    if request.method == 'POST':
        if form.validate_on_submit():
            picture_file = save_picture(form.picture.data)
            path = os.path.join('flaskblog/static/profile_pics', picture_file)
            # print(path)
            # path = '.' + url_for('static', filename='profile_pics/' + picture_file)
            # print(path)
            open_path(path, bucketname=bucketname)
            image = Image.open(path)
            image = image.resize((SIZE, SIZE))
            image = np.array(image)
            if image.shape == (SIZE, SIZE):
                print(image.shape)
                image = image[np.newaxis, :, :, np.newaxis]
                print(image.shape)
                image = image.repeat(3, 3)
                print(image.shape)
            else:
                image = image[np.newaxis, :, :, :]

            image = np.array(image, dtype='float32')
            pred = 3.5 * (model.predict(image)[0][0] - 0.05)
            print(pred)
            pneumonia = divide(pred)
            xray = Xray(name=form.name.data, age=form.age.data, pic_address=picture_file, sex=form.sex.data,
                        pneumonia=pneumonia, exposure_year=form.exposure_year.data, smoke=form.smoke.data,
                        drink=form.drink.data, author=current_user)
            db.session.add(xray)
            db.session.commit()

            flash('您的胸片成功上传', 'success')
            return redirect(url_for('account'))

    image_file = url_for('static', filename='default.jpeg')
    print('image_file', image_file)
    return render_template('diagnose.html', title='diagnose', image_file=image_file, form=form)


@app.route("/account", methods=['GET'])
@login_required
def account():
    image_files = []
    dates = []
    results = []
    ids = []
    Xrays = Xray.query.filter_by(user_id=current_user.id)
    for Xray_ in Xrays:
        image_file = url_for('static', filename='profile_pics/' + Xray_.pic_address)
        image_path = os.path.join('flaskblog/static/profile_pics', Xray_.pic_address)
        open_path(image_path, bucketname)
        print('account', image_file)
        image_files.append(image_file)
        dates.append(Xray_.date_posted)
        results.append(Xray_.pneumonia)
        ids.append(Xray_.id)
    x = list(zip(reversed(image_files), reversed(dates), reversed(results), reversed(ids)))
    flag = 0
    if x:
        flag = 1
    xray = Xray.query.filter_by(user_id=current_user.id).order_by(Xray.id.desc()).first()
    # xray = xrays[-1]

    if xray:
        # flag1, cnt, lst = get_counsel(xray=xray)
        # txt, _ = get_txt(flag1, cnt)
        dic = {0: '正常', 1: '尘肺Ⅰ期', 2: '尘肺Ⅱ期', 3: '尘肺Ⅲ期'}
        # txt = dic[xray.]
        # session['xray_id'] =
        txt = dic[xray.pneumonia]
        print(txt)
    else:
        return render_template('account.html', img_date_result_id=x, flag=flag, txt='')
    return render_template('account.html', img_date_result_id=x, flag=flag, txt=txt)


@app.route("/details/<post_id>")
@login_required
def details(post_id):
    # xray = Xray.query.filter_by(user_id=current_user.id).order_by(Xray.id).all()[-1]

    xray = Xray.query.filter_by(id=post_id, author=current_user).first_or_404()
    # if xray:
    flag, cnt, lst = get_counsel(xray=xray)
    txt, score = get_txt(flag, cnt)

    return render_template('details.html', xray=xray, lst=lst, flag=flag, txt=txt, score=score, post_id=post_id)


@app.route("/prescriptions/<post_id>")
@login_required
def prescriptions(post_id):
    # xray = Xray.query.filter_by(user_id=current_user.id).order_by(Xray.id).all()[-1]

    xray = Xray.query.filter_by(id=post_id, author=current_user).first_or_404()
    # if xray:
    flag, cnt, lst = get_counsel(xray=xray)
    txt, score = get_txt(flag, cnt)

    return render_template('prescriptions.html', xray=xray, lst=lst, flag=flag, txt=txt, score=score)


def get_txt(flag, cnt):
    if flag == 0:
        score = 20
        txt = '低风险'
    elif flag == 1:
        txt = '中风险'
        score = 50
    else:
        if cnt == 0:
            score = 80
            txt = '尘肺I期'
        elif cnt == 1 or cnt == 2:
            score = 90
            txt = '尘肺II期'
        else:
            score = 100
            txt = '尘肺III期'
    return txt, score


def get_counsel(xray):
    exposure_year = xray.exposure_year
    cnt = 0
    if xray.pneumonia == 0:
        lst = [
            '1、建议减少粉尘暴露，定期随访、复查，积极预防呼吸道疾病的发生',
            '2、建议完善胸部CT，进行下一步医学筛查及监测',
            '3、建议保持良好的生活习惯，采取健康的生活方式。',
        ]
        if exposure_year > 5 and xray.age > 45:
            return 1, cnt, lst
        else:
            return 0, cnt, lst
    else:
        lst_const = [
            '建议完善胸部CT，进行下一步医学筛查及监测。',
            '及时脱离接尘作业环境，定期复查、随访，积极预防呼吸道感染等并发症的发生'
        ]
        lst_condidate = [
            '建议医师给予对症治疗，根据实际情况可采取间断或持续低流量吸氧以纠正缺氧状态，改善肺通气功能和缓解呼吸肌疲劳。',
            '积极控制呼吸系统感染，控制肺内感染',

            '对相应并发症给予对症处理：如慢性肺源性心脏病的治疗:应用强心剂(如洋地黄)、利尿剂(如选用氢氯噻嗪)、血管扩张剂(如选用酚妥拉明、硝普钠)'
            '等措施对症处理；呼吸衰竭的治疗:可采用氧疗、通畅呼吸道(解痉、平喘祛痰等措施)、抗炎、纠正电解质紊乱和酸碱平衡失调等措施综合治疗',

            '进行适当的体育锻炼，加强营养，提高机体抵抗力，进行呼吸肌功能锻炼',
            '养成良好的生活习惯，饮食、起居规律，戒掉不良的生活习惯，如吸烟、酗酒等，提高家庭护理质量',
            '若仍在接尘环境工作，做好个人防护，防止或减少粉尘吸入',
            '注意个人卫生，作业点不吸烟，杜绝将粉尘污染的工作服带回家',
            '建议科学膳食，增加优质高蛋白饮食摄入，多进食高热量、高维生素的清淡食物',
            '建议避免恐惧、焦虑等不良心理，必要时可由心理治疗师专人辅导',
            # '建议不吸烟，同时避免二手烟的吸入'
        ]
        lst = []
        if exposure_year != float(0):
            lst.append(
                f'您的二氧化硅或石棉粉尘暴露史为{int(exposure_year)}年，有{"一定" if exposure_year < 3 else "很高"}'
                f'的风险，建议筛查结核病，患者应通过结核菌素皮肤试验或血液试验进行结核病的筛查')
            cnt += 1
        # if xray.age > 60:
        #     lst.append('建议排查是否有肺结核、肺气肿、慢性阻塞肺病等并发症或合并症，并针对并发症进行相关治疗。')
        #     cnt += 1
        if xray.smoke:
            lst.append('建议戒烟，同时避免二手烟的吸入')
            cnt += 1

        # consult = random.sample(lst_condidate, 5 - cnt)
        consult = random.sample(lst_condidate, 3)
        lst += lst_const
        lst += consult
        L = []

        for index, item in enumerate(lst):
            i = f'{str(index + 1)}、{item}'
            L.append(i)

        return 2, cnt, L


@app.errorhandler(404)
def error_404(error):
    return render_template('404.html'), 404


def send_reset_email(user):
    token = user.get_reset_token()

    msg = Message('Password Reset Request',
                  sender='fangyeqi202106@outlook.com',
                  recipients=[user.email])
    # External to return the full URL.
    msg.body = f'''To reset your password, visit the following link:
    {url_for('reset_token', token=token, _external=True)}

    If you did not make this request then simply ignore this email and no changes will be made.
    '''
    mail.send(msg)


@app.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('已将验证码发送至您的邮箱中，请根据说明重置密码', 'info')
        return redirect(url_for('login'))
    return render_template('reset_request.html', title='Reset Password', form=form)


@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('验证码过期或无效', 'warning')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash('您的密码成功重置，请重新登录', 'success')
        return redirect(url_for('login'))
    return render_template('reset_token.html', title='Reset Password', form=form)


@app.route("/redirect_detail", methods=['GET'])
@login_required
def redirect_detail():
    try:
        last_xray = Xray.query.filter_by(author=current_user).all()[-1]
        post_id = last_xray.id
    except builtins.IndexError:
        return redirect(url_for('account'))
    return redirect(url_for('details', post_id=post_id))


@app.route("/redirect_prescription", methods=['GET'])
@login_required
def redirect_prescription():
    try:
        last_xray = Xray.query.filter_by(author=current_user).all()[-1]
        post_id = last_xray.id
    except builtins.IndexError:
        return redirect(url_for('account'))
    return redirect(url_for('prescriptions', post_id=post_id))


@app.route("/excel", methods=['GET'])
@login_required
def excel():
    return render_template('excel.html')
