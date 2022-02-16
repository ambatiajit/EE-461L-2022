from flask import Flask, render_template, redirect, url_for, request, flash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'


class LoginForm(FlaskForm):
    userid = StringField(label='userID', validators=[DataRequired()])
    password = PasswordField(label='password', validators=[DataRequired(), Length(min=8)])
    submit = SubmitField(label='Log in')


# def customEncrypt(plain_text, num_positions, direction):
#     encrypted_text = list(plain_text)[::-1]
#
#     for i in range(len(encrypted_text)):
#         curr_ascii_val = ord(encrypted_text[i])  # store ascii value
#
#         if direction == 1:  # add
#             new_ascii_val = (curr_ascii_val + num_positions) % 127
#             if new_ascii_val < curr_ascii_val:  # take care of values less than 34
#                 new_ascii_val += 34
#         else:  # subtract
#             new_ascii_val = curr_ascii_val - num_positions
#             if new_ascii_val < 34:  # take care of values less than 34
#                 new_ascii_val += 93
#
#         new_letter = chr(new_ascii_val)
#         encrypted_text[i] = new_letter
#
#     result = ''.join(encrypted_text)  # convert result (list) into string
#
#     return result


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if request.method == "POST":
        userid = form.userid.data       # stores userID entered by user
        password = form.password.data   # stores password entered by user
        # need to encrypt password using customEncrypt
        print(userid, password)
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
