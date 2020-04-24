import os
import secrets
from PIL import Image
from flask import render_template, url_for, flash, redirect, abort, request
from flaskapp.forms import RegistrationForm, LoginForm, UpdateAccountForm
from flaskapp.models import User, Product
from flaskapp import app, db, bcrypt
from flask_login import login_user, current_user, logout_user, login_required
import pickle
import random
# from google.oauth2 import service_account
from flaskapp.recommendations import Recommendations
# import gcsfs
# import numpy as np
# credentials = service_account.Credentials.from_service_account_file(
#     './flaskapp/coe-solutions-215839-c9b1b2b721c8.json')

# credentials = service_account.Credentials.from_service_account_file(os.path.join(
#     os.getcwd(), "coe-solutions-215839-c9b1b2b721c8.json"))
rec_util = Recommendations()

PRODUCTS = {
    '1': {
        'name': 'Samsung Galaxy s9',
        'category': 'Phones',
        'price': 699,
    },
    '2': {
        'name': 'Samsung Galaxy s5',
        'category': 'Phones',
        'price': 649,
    },
    '3': {
        'name': 'Samsung Galaxy M20',
        'category': 'Phones',
        'price': 750
    },
    '4': {
        'name': 'Samsung Galaxy M30s',
        'category': 'Phones',
        'price': 850
    },
    '5': {
        'name': 'iPad Mini',
        'category': 'Tablets',
        'price': 549
    },
    '6': {
        'name': 'iPad Pro',
        'category': 'Tablets',
        'price': 700
    },
    '7': {
        'name': 'iPhone 5S',
        'category': 'Phones',
        'price': 800,
    },
    '8': {
        'name': 'iPad Air',
        'category': 'Tablets',
        'price': 649,
    }

}


def func():
    # fs = gcsfs.GCSFileSystem(project='coe-solutions-215839')
    # today = datetime.date.today()
    # yesterday = today - datetime.timedelta(days=1)
    # today_str = today.strftime("%d-%b-%Y")
    # yesterday_str = yesterday.strftime("%d-%b-%Y")
    # PATH_TODAY = 'click_stream_ai_platform/top-n-dict-'+today_str+'.pkl'
    # PATH_YESTERDAY = 'click_stream_ai_platform/top-n-dict-'+yesterday_str+'.pkl'

    # if fs.exists(PATH_TODAY):
    #     PATH = PATH_TODAY
    #     with fs.open(PATH, 'rb') as f:
    #         top_n = pickle.load(f)
    #         print("[INFO] Using Today's model...")
    # elif(fs.exists(PATH_YESTERDAY)):
    #     PATH = PATH_YESTERDAY
    #     with fs.open(PATH, 'rb') as f:
    #         top_n = pickle.load(f)
    #         print("[INFO] Using Yesterday's model...")
    # else:
    #     PATH = './top-n.pkl'
    #     with open(PATH, 'rb') as fid:
    #         top_n = pickle.load(fid)
    #         print("[INFO] Using local model...")
    pass


PATH = './flaskapp/top-n.pkl'
with open(PATH, 'rb') as fid:
    top_n = pickle.load(fid)
    print("[INFO] Using local model...")


@app.route('/')
def default():
    if current_user.is_authenticated:
        return redirect(url_for('home', uname=current_user.username, uid=current_user.id))
    else:
        return render_template('default.html', title='Default')


@app.route('/home/<uname>/<uid>', methods=["GET", "POST"])
@login_required
def home(uname, uid):
    user_id = current_user.id
    n_rec = 4
    # rec_list = rec_util.get_recommendations(user_id, n_rec)
    rec_list = [3, 4, 5]
    return render_template('home.html', products=PRODUCTS, uname=current_user.username, uid=user_id, rec_list=rec_list)


@app.route('/login', methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home', uname=current_user.username, uid=current_user.id))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home', uname=current_user.username, uid=current_user.id))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route('/register', methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(
            form.password.data).decode('utf-8')
        user = User(username=form.username.data,
                    email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash(f'Your account has been created! you are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/product/<uname>/<uid>/<pname>/<iid>')
@login_required
def product(uname, uid, pname, iid):
    product = PRODUCTS.get(iid)
    prod_dict = PRODUCTS
    rnd_itm = random.choice([3, 4, 5, 6])
    top_n_1 = top_n[rnd_itm]
    if not product:
        abort(404)
    return render_template('product.html', product=product, top_n=top_n_1, prod_dict=prod_dict)


@app.route('/about')
def about():
    return render_template('about.html')


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('default'))


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    f_name, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(
        app.root_path, 'static', 'profile_pics', picture_fn)
    # form_picture.save(picture_path)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for(
        'static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account', image_file=image_file, form=form)
