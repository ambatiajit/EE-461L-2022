from flask import Flask, render_template, redirect, url_for, request, flash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
import certifi
from user import User

NUM_POSITIONS = 3       # number of positions to shift characters in a user's password
DATABASE_PASSWORD = "kltlFKZqaaj4jZCX"

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'

# create a login manager
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user):
    # print(f"The current user is {user}.")
    # print(user['first_name'], user['last_name'])
    return user_manager.find_one(user)
    # return db.session.query(User).get(int(user_id))

# create client object database
client = MongoClient(f"mongodb+srv://teamMember:{DATABASE_PASSWORD}@usermanagement.zcdlh.mongodb.net/myFirstDatabase?retryWrites=true&w=majority&tlsCAFile={certifi.where()}")
projectdb = client['projectdb']
# Make 3 separte collections within the project database: user, project, and hardware
user_manager = projectdb['Users']
project_manager = projectdb['Projects']
hardware_manager = projectdb['HWSet']


class LoginForm(FlaskForm):
    userid = StringField(label='userID', validators=[DataRequired()])
    password = PasswordField(label='password', validators=[DataRequired()])
    submit = SubmitField(label='Log in')


class RegisterForm(FlaskForm):
    fname = StringField(label='First name', validators=[DataRequired()])
    lname = StringField(label='Last name', validators=[DataRequired()])
    userid = StringField(label='userID', validators=[DataRequired()])
    password = PasswordField(label='password', validators=[DataRequired()])
    submit = SubmitField(label='Sign up')


def custom_encrypt(plain_text, direction):
    global NUM_POSITIONS
    encrypted_text = list(plain_text)[::-1]

    for i in range(len(encrypted_text)):
        curr_ascii_val = ord(encrypted_text[i])  # store ascii value

        if direction == 1:  # add
            new_ascii_val = (curr_ascii_val + NUM_POSITIONS) % 127
            if new_ascii_val < curr_ascii_val:  # take care of values less than 34
                new_ascii_val += 34
        else:  # subtract
            new_ascii_val = curr_ascii_val - NUM_POSITIONS
            if new_ascii_val < 34:  # take care of values less than 34
                new_ascii_val += 93

        new_letter = chr(new_ascii_val)
        encrypted_text[i] = new_letter

    result = ''.join(encrypted_text)  # convert result (list) into string
    return result


@app.route('/')
def home():
    return render_template('index.html', logged_in=current_user.is_authenticated)


@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if request.method == "POST":
        userid = form.userid.data       # stores userID entered by user
        password = form.password.data   # stores password entered by user

        # need to check if username and password exists in database
        encrypted_password = custom_encrypt(password, 1)
        user = user_manager.find_one({"userID": userid})

        # user does not exist or password entered is incorrect
        if not user or user['encr_pwd'] != encrypted_password:
            error = "The username or password you entered is incorrect."
            flash(error)
            return redirect(url_for('login'))

        # user exists --> login user
        else:
            # user_to_login = User()
            # user_to_login.id = user['userID']
            # login_user(user_to_login)
            print(f"Welcome, {user['first_name']} {user['last_name']}!")
            return redirect(url_for('home'))

    return render_template('login.html', form=form, logged_in=current_user.is_authenticated)


@app.route('/register', methods=["GET", "POST"])
def register():
     form = RegisterForm()     # make register form class
     if request.method == "POST":
         fname = form.fname.data    # stores first name entered by user
         lname = form.lname.data    # stores last name entered by user
         userid = form.userid.data  # stores userID entered by user
         password = form.password.data  # stores password entered by user
         encrypted_password = custom_encrypt(password, 1)    # encrypt the password entered by user

         # put user's information into MongoDB database
         post = {'first_name':fname,
                 'last_name':lname,
                 'userID': userid,
                 'pwd': password,
                 'encr_pwd': encrypted_password}

         print(post)
         print(password == custom_encrypt(encrypted_password, -1))
         user_manager.insert_one(post)
         return redirect(url_for('home'))

     return render_template('register.html', form=form, logged_in=current_user.is_authenticated)


@app.route('/resources')
def resources():
    return render_template('resources.html')


@app.route('/projects')
def projects():
    return render_template('projects.html')


@app.route('/data_access')
def data_access():
    return render_template('data_access.html')


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
