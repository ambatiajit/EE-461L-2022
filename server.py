from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_wtf import FlaskForm
from matplotlib.style import available
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Email, Length
from pymongo import MongoClient
import certifi

NUM_POSITIONS = 3       # number of positions to shift characters in a user's password
DATABASE_PASSWORD = "kltlFKZqaaj4jZCX"

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'

# create client object database
client = MongoClient(f"mongodb+srv://teamMember:{DATABASE_PASSWORD}@usermanagement.zcdlh.mongodb.net/myFirstDatabase?retryWrites=true&w=majority&tlsCAFile={certifi.where()}")
projectdb = client['projectdb']

# store the 3 separate collections within the project database in 3 different variables
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

class CheckInOutForm(FlaskForm):
    item = StringField(label='Item name', validators=[DataRequired()])
    quantity = StringField(label='Quantity', validators=[DataRequired()])
    in_out = BooleanField(label = "In or out")
    submit = SubmitField(label='Submit')

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
    logged_in = is_logged_in()
    return render_template('index.html', logged_in=logged_in)


@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if request.method == "POST":
        userid = form.userid.data           # stores userID entered by user
        password = form.password.data       # stores password entered by user

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
            login_user(user['userID'], user['first_name'], user['last_name'])
            return redirect(url_for('home'))

    return render_template('login.html', form=form)


@app.route('/register', methods=["GET", "POST"])
def register():
     form = RegisterForm()     # make register form class
     if request.method == "POST":
         fname = form.fname.data    # stores first name entered by user
         lname = form.lname.data    # stores last name entered by user
         userid = form.userid.data  # stores userID entered by user
         password = form.password.data  # stores password entered by user
         encrypted_password = custom_encrypt(password, 1)    # encrypt the password entered by user

         # check for invalid characters in userid and password ('!' and ' ')
         if ' ' in userid or '!' in userid:
             error = "Passwords cannot contain '!' or ' '."
             flash(error)
             return redirect(url_for('register'))

         if ' ' in password or '!' in password:
             error = "Passwords cannot contain '!' or ' '."
             flash(error)
             return redirect(url_for('register'))

         # put user's information into MongoDB database & log in the user
         post = {'first_name':fname,
                 'last_name':lname,
                 'userID': userid,
                 'encr_pwd': encrypted_password,                # only store encrypted password in database
                 'resources': {'HWSet1': 0, 'HWSet2': 0},       # initially has 0 resources
                 'projects': []}                                # array that contains projectIDs, initially empty

         user_manager.insert_one(post)
         login_user(userid, fname, lname)
         return redirect(url_for('home'))

     return render_template('register.html', form=form)


@app.route('/resources', methods=["GET", "POST"])
def resources():
    logged_in = is_logged_in()

    check_in_out_form = CheckInOutForm()

    print("res func ")

    if check_in_out_form.validate_on_submit():

        #if check in box checked
        if check_in_out_form.in_out.data:   
        
            # stores set name entered by user
            item = check_in_out_form.item.data  
            # stores quantity requested by user
            quantity = int(check_in_out_form.quantity.data) 
            
            set = hardware_manager.find_one({"Name": item})
            availability = set["Availability"]

            # if avail. + quantity to be returned exceeds max capacity
            if (set["Capacity"] < availability + quantity) or quantity < 1:
                error = "invalid quantity"
                flash(error)
            # set has space for items being returned
            else:
                availability += quantity

            # put updated set information into MongoDB database
            set["Availability"] = availability
            hardware_manager.update_one({'Name':set["Name"]}, {"$set": set}, upsert=False)

            #refresh page and reset fields  
            return redirect(url_for('resources'))

        else:
            # stores set name entered by user
            item = check_in_out_form.item.data
            # stores quantity requested by user
            quantity = int(check_in_out_form.quantity.data)
            
            set = hardware_manager.find_one({"Name": item})
            availability = set["Availability"]

            # if set has less avail. than quantity requested
            if availability < quantity or quantity < 1:
                error = "invalid quantity"
                flash(error)
            # set has quantity requested or more
            else:
                availability -= quantity

            # put updated set information into MongoDB database
            set["Availability"] = availability
            hardware_manager.update_one({'Name':set["Name"]}, {"$set": set}, upsert=False)

            #refresh page and reset fields  
            return redirect(url_for('resources'))

    return render_template('resources.html', logged_in=logged_in, hardware_manager = hardware_manager, check_in_out_form = check_in_out_form)


@app.route('/projects')
def projects():
    logged_in = is_logged_in()

    return render_template('projects.html', logged_in=logged_in)


@app.route('/data_access')
def data_access():
    logged_in = is_logged_in()

    return render_template('data_access.html', logged_in=logged_in)


@app.route('/logout')
def logout():
    session.clear()                     # clear the current session and logout the user
    return redirect(url_for('home'))


""" This method logs in a user by setting the properties of session """
def login_user(userid, fname, lname):
    session['userID'] = userid
    session['first_name'] = fname
    session['last_name'] = lname


def is_logged_in():
    if 'userID' in session:
        return True
    return False


if __name__ == '__main__':
    app.run(debug=True)
