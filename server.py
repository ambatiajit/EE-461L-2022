from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired
from pymongo import MongoClient
import certifi

from IPython.display import display
import wfdb

NUM_POSITIONS = 3  # number of positions to shift characters in a user's password
DATABASE_PASSWORD = "kltlFKZqaaj4jZCX"

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'

# create client object database
client = MongoClient(
    f"mongodb+srv://teamMember:{DATABASE_PASSWORD}@usermanagement.zcdlh.mongodb.net/myFirstDatabase?retryWrites=true&w=majority&tlsCAFile={certifi.where()}")
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
    project = StringField(label='ProjectID', validators=[DataRequired()])
    in_out = BooleanField(label="In or out")
    submit = SubmitField(label='Submit')


class CreateNewProjectForm(FlaskForm):
    project_name = StringField(label='Project Name', validators=[DataRequired()])
    project_description = StringField(label='Project Description', validators=[DataRequired()])
    project_id = StringField(label='Project ID', validators=[DataRequired()])
    submit = SubmitField(label='Create')


class JoinExistingProjectForm(FlaskForm):
    id = StringField(label='Project ID', validators=[DataRequired()])
    submit = SubmitField(label='Join')


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
        userid = form.userid.data  # stores userID entered by user
        password = form.password.data  # stores password entered by user

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
    form = RegisterForm()  # make register form class
    if request.method == "POST":
        fname = form.fname.data  # stores first name entered by user
        lname = form.lname.data  # stores last name entered by user
        userid = form.userid.data  # stores userID entered by user
        password = form.password.data  # stores password entered by user
        encrypted_password = custom_encrypt(password, 1)  # encrypt the password entered by user

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
        post = {'first_name': fname,
                'last_name': lname,
                'userID': userid,
                'encr_pwd': encrypted_password,  # only store encrypted password in database
                'projects': []}  # array that contains projectIDs, initially empty

        user_manager.insert_one(post)
        login_user(userid, fname, lname)
        return redirect(url_for('home'))

    return render_template('register.html', form=form)


@app.route('/resources', methods=["GET", "POST"])
def resources():
    set_names = ["HWSet1", "HWSet2"]
    logged_in = is_logged_in()

    #                 user_data = user_manager.find_one({"userID": session['userID']})
    user_projects = []
    if logged_in:               # need to store user's projects
        user_projects = user_manager.find_one({'userID': session['userID']})['projects']

    check_in_out_form = CheckInOutForm()

    if check_in_out_form.is_submitted() and logged_in:
        set_name = check_in_out_form.item.data
        project_id = check_in_out_form.project.data

        if set_name not in set_names:       # user enters something other than 'HWSet1' or 'HWSet2' c
            error = "That hardware set does not exist."
            flash(error)
        elif project_id not in user_projects:
            error = "That project either does not exist or your are not logged in to that project."
            flash(error)
        else:           # checking in/out hardware to project with id of project_id
            curr_project = project_manager.find_one({'ID': project_id})     # current project to check in/out HW from
            # if check in box checked
            if check_in_out_form.in_out.data:
                # stores set name entered by user
                item = check_in_out_form.item.data
                # stores quantity requested by user
                quantity = int(check_in_out_form.quantity.data)

                hwset = hardware_manager.find_one({"Name": item})
                availability = hwset["Availability"]

                amount_in_project = 0
                if item == 'HWSet1':
                    amount_in_project = curr_project['HW'][0]
                elif item == 'HWSet2':
                    amount_in_project = curr_project['HW'][1]

                # user_data = user_manager.find_one({"userID": session['userID']})

                # if avail. + quantity to be returned exceeds max capacity
                if (hwset["Capacity"] < availability + quantity) or quantity < 1:
                    error = "Invalid quantity."
                    flash(error)
                elif amount_in_project < quantity:   # check if user has enough to check in qty
                    # error = f"You only have {amount_in_project} hardware."
                    error = f"You don't have enough hardware to check in."
                    flash(error)
                # set has space for items being returned
                else:
                    availability += quantity
                    amount_in_project -= quantity

                    if item == 'HWSet1':
                        curr_project['HW'][0] = amount_in_project
                    elif item == 'HWSet2':
                        curr_project['HW'][1] = amount_in_project

                    project_manager.update_one({'ID': project_id}, {'$set': curr_project})

                    # user_data['resources'][set_name] -= quantity
                    # user_manager.update_one({'userID': session['userID']}, {'$set': user_data})

                # put updated set information into MongoDB database & update user's resources
                hwset["Availability"] = availability
                # user resources -= qty
                hardware_manager.update_one({'Name': hwset["Name"]}, {"$set": hwset}, upsert=False)

                # refresh page and reset fields
                return redirect(url_for('resources'))

            else:           # checking out hardware
                # stores set name entered by user
                item = check_in_out_form.item.data
                # stores quantity requested by user
                quantity = int(check_in_out_form.quantity.data)

                hwset = hardware_manager.find_one({"Name": item})
                availability = hwset["Availability"]

                amount_in_project = 0
                if item == 'HWSet1':
                    amount_in_project = curr_project['HW'][0]
                elif item == 'HWSet2':
                    amount_in_project = curr_project['HW'][1]

                check_out_quantity = quantity       # only updated if set has less availability than quantity requested

                # if set has less availability than quantity requested
                if availability < quantity or quantity < 1:
                    error = f"{item} only has {availability} hardware available, you were only able to check out " \
                            f"{availability}."
                    flash(error)
                    check_out_quantity = availability
                    availability = 0        # check out what is available
                # set has quantity requested or more
                else:
                    availability -= quantity

                # put updated set information into MongoDB database & update user's resources
                hwset["Availability"] = availability
                hardware_manager.update_one({'Name': hwset["Name"]}, {"$set": hwset}, upsert=False)

                if item == 'HWSet1':
                    curr_project['HW'][0] += check_out_quantity
                elif item == 'HWSet2':
                    curr_project['HW'][1] += check_out_quantity
                project_manager.update_one({'ID': project_id}, {'$set': curr_project})

                # user_data = user_manager.find_one({"userID": session['userID']})
                # user_data['resources'][set_name] += check_out_quantity
                # user_manager.update_one({'userID': session['userID']}, {'$set': user_data})

                # refresh page and reset fields
                return redirect(url_for('resources'))

    return render_template('resources.html', logged_in=logged_in, hardware_manager=hardware_manager,
                           project_manager=project_manager, check_in_out_form=check_in_out_form, user_projects=user_projects)
    # return render_template('resources.html', logged_in=logged_in, hardware_manager=hardware_manager,
    #                        project_manager=project_manager, check_in_out_form=check_in_out_form, hwset1=user_hwset1,
    #                        hwset2=user_hwset2)


@app.route('/projects', methods=['GET', 'POST'])
def projects():
    logged_in = is_logged_in()
    create_new_project_form = CreateNewProjectForm()
    join_existing_project_form = JoinExistingProjectForm()

    all_projects = []
    if logged_in:  # need to store user's projects
        projects = project_manager.find({})
        for project in projects:
            all_projects.append(project['ID'])

    if request.method == "POST":
        if not create_new_project_form.project_name.data:    # user is joining a project --> check for valid project id
            requested_project_id = join_existing_project_form.id.data
            if requested_project_id not in all_projects:
                error = "There is no such project with the project ID you entered."
                flash(error)
                return redirect(url_for('projects'))
            else:               # join the user to the requested project (if not already joined)
                current_user_projects = user_manager.find_one({'userID': session['userID']})['projects']
                if requested_project_id in current_user_projects:      # user is already joined to the requested project
                    error = "You have already joined the requested project."
                    flash(error)
                    return redirect(url_for('projects'))
                else:           # add project to user's projects
                    current_user = user_manager.find_one({'userID': session['userID']})
                    # print('current projects:', current_user['projects'])
                    current_user_projects.append(requested_project_id)
                    # print("updated user's projects:", current_user_projects)

                    current_user['projects'] = current_user_projects
                    user_manager.update_one({'userID': session['userID']}, {'$set': current_user})
                    success = f"You have successfully joined the project with a projectID of {requested_project_id}!"
                    flash(success)
                    return redirect(url_for('projects'))

        else:       # user is creating a new project --> create new project + automatically join user to that project
            # insert new project into project_manager
            new_project_name = create_new_project_form.project_name.data
            new_project_id = create_new_project_form.project_id.data
            new_project_description = create_new_project_form.project_description.data

            # first check if new_project_id is an existing ID (ID's must be unique)
            if new_project_id in all_projects:
                error = "That project ID already exists, please enter a new one."
                flash(error)
                return redirect(url_for('projects'))
            else:
                new_project = {
                    'Name': new_project_name,
                    'ID': new_project_id,
                    'Description': new_project_description,
                    'HW': [0, 0]
                }
                project_manager.insert_one(new_project)

                # join the current user to the created project
                current_user = user_manager.find_one({'userID': session['userID']})
                current_user_projects = current_user['projects']

                current_user_projects.append(new_project_id)
                current_user['projects'] = current_user_projects
                user_manager.update_one({'userID': session['userID']}, {'$set': current_user})

                return redirect(url_for('projects'))

    return render_template('projects.html', logged_in=logged_in, project_manager=project_manager,
                           create_new_project_form=create_new_project_form, join_existing_project_form=join_existing_project_form)


@app.route('/data_access')
def data_access():
    logged_in = is_logged_in()

    # Read a WFDB record using the 'rdrecord' function into a wfdb.Record object.
    record = wfdb.rdrecord('af-termination-challenge-database-1.0.0/learning-set/n01')

    display(record.__dict__)
    dict = record.__dict__

    return render_template('data_access.html', logged_in=logged_in, dict=dict)


@app.route('/logout')
def logout():
    session.clear()  # clear the current session and logout the user
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
