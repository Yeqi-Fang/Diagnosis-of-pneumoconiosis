import os
import secrets
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, session
from . import app, db, bcrypt, mail
from flaskblog.forms import RegistrationForm, LoginForm, Diagnosis, RequestResetForm, ResetPasswordForm
from flaskblog.models import User, Xray
from flask_login import login_user, current_user, logout_user, login_required
import cv2
import numpy as np
from tensorflow.keras.applications import VGG16
from tensorflow.keras.layers import Dense, Dropout, Flatten
from tensorflow.keras.models import Sequential
from tensorflow.keras import optimizers
from flask_mail import Message

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

SIZE = 150
conv_base = VGG16(weights='imagenet',
                  include_top=False,
                  input_shape=(SIZE, SIZE, 3))
conv_base.trainable = False
model = Sequential()
model.add(conv_base)
model.add(Flatten(input_shape=conv_base.output_shape[1:]))
model.add(Dense(256, activation='relu'))
model.add(Dropout(0.5))
model.add(Dense(2, activation='softmax'))
model.compile(optimizer=optimizers.Adam(lr=0.0005 / 100),
              loss='mse',
              metrics=['accuracy'])
model.load_weights("flaskblog/model.hdf5")


@app.route("/home")
def home():
    # posts = Post.query.all()
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


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)
    i = Image.open(form_picture)
    i.save(picture_path)
    return picture_fn


@app.route('/', methods=['GET', 'POST'])
@app.route("/diagnosis", methods=['GET', 'POST'])
@login_required
def diagnosis():
    form = Diagnosis()
    if request.method == 'POST':
        picture_file = save_picture(form.picture.data)
        path = os.path.join(
            'flaskblog\\static\\profile_pics',
            picture_file)
        print(path)
        image = cv2.imread(path)
        image = cv2.resize(image, (150, 150))

        image = image[np.newaxis, :, :, :]
        image = np.array(image, dtype='float16')
        pred = model.predict(image)
        PNEUMONIA = bool(np.round(pred[:, 1][0]))
        xray = Xray(name=form.name.data, age=form.age.data, pic_address=picture_file, sex=form.sex.data,
                    PNEUMONIA=PNEUMONIA, exposure_year=form.exposure_year.data, smoke=form.smoke.data,
                    author=current_user)
        db.session.add(xray)
        db.session.commit()

        flash('您的胸片成功上传', 'success')
        return redirect(url_for('account'))

    image_file = url_for('static', filename='default.jpeg')
    print('image_file', image_file)
    return render_template('diagnose.html', title='diagnose',
                           image_file=image_file, form=form)


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
        print('account', image_file)
        image_files.append(image_file)
        dates.append(Xray_.date_posted)
        results.append(Xray_.PNEUMONIA)
        ids.append(Xray_.id)
    x = list(zip(reversed(image_files), reversed(dates), reversed(results), reversed(ids)))
    flag = 0
    if x:
        flag = 1
    xray = Xray.query.filter_by(user_id=current_user.id).order_by(Xray.id.desc()).first_or_404()
    # xray = xrays[-1]
    flag1, cnt, lst = get_counsel(xray=xray)
    txt, _ = get_txt(flag1, cnt)
    # session['xray_id'] =
    return render_template('account.html', img_date_result_id=x, flag=flag, txt=txt)


@app.route("/details/<post_id>")
@login_required
def details(post_id):
    # xray = Xray.query.filter_by(user_id=current_user.id).order_by(Xray.id).all()[-1]

    xray = Xray.query.filter_by(id=post_id, author=current_user).first_or_404()
    # if xray:
    flag, cnt, lst = get_counsel(xray=xray)
    txt, score = get_txt(flag, cnt)

    return render_template('details.html', xray=xray, lst=lst, flag=flag, txt=txt, score=score)


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
    if not xray.PNEUMONIA:
        lst = [
            '1、建议定期复查，出入含粉尘场所做好防护措施，避免接触职业性或生活性粉尘。替换工作中的粉尘材料，消除粉尘暴露',
            '2、建议应用合理的劳动保护措施，施工时，使用防护系数高的呼吸器',
            '3、建议完善胸部CT，进行下一步筛查。',
            '4、建议保持良好的生活习惯，采取健康的生活方式。'
        ]
        if exposure_year > 5 and xray.age > 45:
            return 1, cnt, lst
        else:
            return 0, cnt, lst
    else:
        lst = [
            '建议采取药物治疗，可采用扩张支气管的药物来缓解患者出现的呼吸困难等问题。建议使用抗感染的药物进行对应炎症的治疗。建议进行尘肺抗纤维化的治疗。',
            '建议预防感冒、呼吸道及肺部感染，做好自我管理，预防并发症感染，防止肺心病急性加重。',
            '建议科学膳食，增加优质高蛋白饮食如蛋类、奶类、瘦肉等的摄入，保证营养。',
            '建议避免恐惧、焦虑等不良心理，必要时可由心理治疗师专人辅导',
            '建议采取呼吸康复训练，包括呼吸控制训练、呼吸肌训练、轮廓放松训练、咳嗽训练、体位排痰法等。同时可进行适当运动。'
        ]
        if exposure_year == float(0):
            pass
        else:
            lst.append(
                f'您的二氧化硅或石棉粉尘暴露史为{exposure_year}，有{"一定" if exposure_year < 3 else "很高"}'
                f'的风险，建议筛查结核病，患者应通过结核菌素皮肤试验或血液试验进行结核病的筛查')
            cnt += 1
        if xray.age > 60:
            lst.append('建议排查是否有肺结核、肺气肿、慢性阻塞肺病等并发症或合并症，并针对并发症进行相关治疗。')
            cnt += 1
        if xray.smoke:
            lst.append('建议戒烟，同时避免二手烟的吸入')
            cnt += 1
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
