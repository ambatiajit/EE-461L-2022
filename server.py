import pymongo
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient

# global constants
NUM_POSITIONS = 3       # number of positions to shift characters in a user's password
DATABASE_PASSWORD = "Lalakers2324"

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
# user_db_password = 'G6zaqxfrbylpiTda'

# create client object database
client = MongoClient(f"mongodb+srv://ee461LTeamGroup1:<{DATABASE_PASSWORD}>@usermanagement.zcdlh.mongodb.net/test?retryWrites=true&w=majority")
projectdb =  client['projectdb']

user_manager = projectdb['users']
project_manager = projectdb['projects']
hardware_manager = projectdb['hardware']


class LoginForm(FlaskForm):
    userid = StringField(label='userID', validators=[DataRequired()])
    password = PasswordField(label='password', validators=[DataRequired(), Length(min=8)])
    submit = SubmitField(label='Log in')


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
    return render_template('index.html')


@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if request.method == "POST":
        userid = form.userid.data       # stores userID entered by user
        password = form.password.data   # stores password entered by user
        encrypted_password = custom_encrypt(password, 1)    # need to encrypt password using customEncrypt

        # put userID and encrypted password into projectdb (users)
        post = {'userID': userid, 'password': encrypted_password}
        print(post)
        # user_manager.insert_one(post)
        # return redirect(url_for('home'))

    return render_template('login.html', form=form)


@app.route('/register', methods=["GET", "POST"])
def register():
    return render_template('register.html')


@app.route('/resources')
def resources():
    return render_template('resources.html')


@app.route('/projects')
def projects():
    return render_template('projects.html')


@app.route('/data_access')
def data_access():
    return render_template('data_access.html')


if __name__ == '__main__':
    app.run(debug=True)
