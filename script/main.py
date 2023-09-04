import smtplib
from score import Score
import os

from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

import ssl
import random
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from toConnect import toConnect

# Driver object and authority
app = Flask(__name__)
app.app_context().push()
# Score calculation object
score_calc = None

# Login security measures
two_step_code = None
login_attempted = False
granted_login = False

# Sign up security measures
email_code = None
signup_attempted = False
granted_signup = False

# Username and password if signup
username = None
password = None
email = None

# Starting point and destination
starting_point = None
destination = None

# CREATE DATABASE
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///books.db"

# Optional: But it will silence the deprecation warning in the console.
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# CREATE TABLE
class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250), unique=True, nullable=False)
    email = db.Column(db.String(250), unique=True, nullable=False)


db.create_all()


@app.route("/", methods=['GET', 'POST'])
def load():
    reset()
    return render_template("login.html")


@app.route("/login", methods=['GET', 'POST'])
def login():
    # Global variables
    global username, password, email

    if request.method == 'POST':
        # Input for username and password
        login_user = str(request.form.get("username"))
        login_pass = str(request.form.get("password"))

        # Check if such login exists
        login = Users.query.filter_by(username=login_user).first()
        login_exists = db.session.query(Users.id).filter_by(username=login_user).first()

        if login_exists:
            email = login.email

            # Correct password
            if login.password == login_pass:
                # Get username and password
                username = login_user
                password = login_pass

                # Send email for verification
                send_email(email, "Login")
                return render_template("verify.html")

            # Incorrect password
            else:
                return render_template("login.html", invalid_combo=True)

        # Login doesn't exist
        else:
            return render_template("login.html", invalid_combo=True)
    else:
        return render_template("login.html", invalid_combo=False)


@app.route("/verify", methods=['GET', 'POST'])
def verify():
    # Global variables
    global username, password, email
    global two_step_code

    if username is not None and password is not None and email is not None:
        if request.method == 'POST':
            code = str(request.form.get("code"))

            # Correct 2 step verification code
            if code == two_step_code:
                return render_template("questions.html", valid_gender=True, valid_age=True, valid_years=True,
                                       valid_previous_crashes=True, valid_years_car=True)

            # Incorrect verification code
            else:
                return render_template("verify.html", invalid_code=True)
        else:
            return render_template("verify.html", invalid_code=False)
    else:
        return redirect(url_for("load"))


@app.route("/survey", methods=['GET', 'POST'])
def survey():
    # Global variables
    global username, password, email
    global two_step_code, score_calc

    if username is not None and password is not None and email is not None and two_step_code is not None:
        if request.method == 'POST':
            # Inputs from fields
            enter_name = str(request.form.get("name"))
            enter_gender = str(request.form.get("gender"))
            enter_age = int(str(request.form.get("age")))
            enter_years = int(str(request.form.get("yearsdrive")))
            enter_previous_crashes = int(str(request.form.get("crashes")))
            enter_years_car = int(str(request.form.get("yearscar")))

            # Validity of inputs
            valid_name = (len(enter_name) > 0)
            valid_gender = (enter_gender.upper() == 'M' or enter_gender.upper() == 'F')
            valid_age = (16 <= enter_age <= 99)
            valid_years = (0 <= enter_years <= 70)
            valid_previous_crashes = (0 <= enter_previous_crashes)
            valid_years_car = (0 <= enter_years_car)

            # If inputs valid, calculate
            if valid_name and valid_gender and valid_age and valid_years and \
                    valid_previous_crashes and valid_years_car:
                # Calculation method
                score_calc = Score(enter_name, enter_age, enter_gender, enter_years, enter_previous_crashes,
                                   enter_years_car)
                return render_template("map.html")

            # Inputs invalid, return and throw error
            else:
                return render_template("questions.html", valid_gender=valid_gender, valid_age=valid_age,
                                       valid_years=valid_years,
                                       valid_previous_crashes=valid_previous_crashes, valid_years_car=valid_years_car)
        else:
            return render_template("questions.html", valid_gender=True, valid_age=True, valid_years=True,
                                   valid_previous_crashes=True, valid_years_car=True)

    # If invalid fields, reload to main
    else:
        return redirect(url_for("load"))


@app.route("/map", methods=['GET', 'POST'])
def map():
    # Global variables
    global username, password, email
    global two_step_code, score_calc
    global starting_point, destination

    if username is not None and password is not None and email is not None and \
            two_step_code is not None and score_calc is not None:
        if request.method == 'POST':
            starting_point = str(request.form.get("start"))
            destination = str(request.form.get("finish"))
            score = score_calc.total_score
            map, route, zoom, bbox, heat_map = get_route_map(starting_point, destination, score)
            # print(route)
            import folium
            # import folium to create the map
            from branca.element import Figure
            fig = Figure(width=1024, height=2056)
            # defined the map
            m1 = folium.Map(width=1024, height=2056, location=map, zoom_start=int(zoom - 1), min_zoom=1,
                            max_zoom=20)
            fig.add_child(m1)
            color = [ 'blue',  'purple', 'orange', 'darkred', 'lightred', 'beige', 'darkblue', 'darkgreen', 'cadetblue', 'darkpurple', 'white', 'pink', 'lightblue', 'lightgreen', 'gray', 'black', 'lightgray']
            for i in range(0, len(route["features"])):
                coords = route["features"][i]["geometry"]["coordinates"]
                markers = []
                for coor in coords:
                    markers.append([coor[1], coor[0]])
                # print(markers)

                # add the map to figure
                f1 = folium.FeatureGroup(f"Path{i}")
                line_1 = folium.vector_layers.PolyLine(markers, popup=f'<b>path{i}</b>', tooltip=f'path{i}', color=color[i],
                                                       weight=7).add_to(f1)
                f1.add_to(m1)
            # folium.LayerControl().add_to(m1)
            # add the path

            from folium import plugins
            from folium.plugins import HeatMap
            # creating heatmap data
            heat_data = []
            for location in heat_map.keys():
                heat_data.append([location[0],location[1], heat_map[location]])

            HeatMap(heat_data).add_to(folium.FeatureGroup(name='Heat Map').add_to(m1))


            # add bounding boxed
            for box in bbox:
                folium.Rectangle([(box.north,box.west),(box.south,box.east)]).add_to(m1)

            folium.LayerControl().add_to(m1)






            out_path = os.path.join("templates","out.html")
            if os.path.exists(out_path):
                os.remove(out_path)

            import webbrowser
            m1.save(out_path)

            return render_template("out.html")

        else:
            return render_template( "out.html", invalid=False)

    # If invalid fields, reload to main
    else:
        return redirect(url_for("load"))


@app.route("/signup", methods=['GET', 'POST'])
def signup():
    # Global variables
    global username, password, email

    if request.method == 'POST':
        # Fields for signup
        username = str(request.form.get("username"))
        password = str(request.form.get("password"))
        email = str(request.form.get("email"))

        # See if fields exist or password is valid
        username_exists = db.session.query(Users.id).filter_by(username=username).first() is not None
        password_exists = db.session.query(Users.id).filter_by(password=password).first() is not None
        email_exists = db.session.query(Users.id).filter_by(email=email).first() is not None
        password_valid = evaluate_password(password)

        # Throw errors if needed
        if username_exists or password_exists or email_exists:
            return render_template("signup.html", username_exists=username_exists, password_exists=password_exists,
                                   email_exists=email_exists, password_valid=password_valid)
        else:
            # Password invalid
            if not password_valid:
                return render_template("signup.html", username_exists=username_exists, password_exists=password_exists,
                                       email_exists=email_exists, password_valid=password_valid)
            else:
                # Send email for verification
                send_email(email, "Signup")
                return render_template("signverify.html", code_wrong=False)

    return render_template("signup.html", username_exists=False, password_exists=False,
                           email_exists=False, password_valid=True)


@app.route("/signverify", methods=['GET', 'POST'])
def sign_verify():
    # Global variables
    global username, password, email
    global email_code

    # If fields are not taken
    if username is not None and password is not None and email is not None:
        if request.method == 'POST':
            code = str(request.form.get("code"))

            # Add to database if codes are equal
            if code == email_code:
                user = Users(username=username, password=password, email=email)

                # Add to database and refresh
                try:
                    db.session.add(user)
                    db.session.commit()
                except:
                    return render_template("signverify.html", code_wrong=True)

                return redirect(url_for("load"))

            # Throw error
            else:
                return render_template("signverify.html", code_wrong=True)

        return render_template("signverify.html")

    # If invalid fields, reload to main
    else:
        return redirect(url_for("load"))


@app.route("/forgot", methods=['GET', 'POST'])
def forgot():
    # Global variables
    global username, password, email

    if request.method == 'POST':
        # Get email
        email = str(request.form.get("email"))
        email_exists = db.session.query(Users.id).filter_by(email=email).first() is not None

        if email_exists:
            try:
                # Email to change
                to_change = Users.query.filter_by(email=email).first()

                # Get username and password
                username = to_change.username
                password = to_change.password

                # Send recovery email
                send_email(email, "Recovery")
            except:
                return render_template("changepassword.html", invalid_email=False)

            return render_template("changepassword.html", invalid_email=False)

        # Email is invalid
        else:
            return render_template("forgot.html", invalid_email=True)
    else:
        return render_template("forgot.html", invalid_email=False)


@app.route("/changepassword", methods=['GET', 'POST'])
def change_password():
    # Global variables
    global email, username, password

    if email is not None:
        if request.method == 'POST':
            # Fields to change password
            old_password = str(request.form.get("oldpassword"))
            temp_password = str(request.form.get("password"))
            re_password = str(request.form.get("repassword"))

            # If old password doesn't match
            if password != old_password:
                return render_template("changepassword.html", old_wrong=True, no_match=True, invalid=False, taken=False)

            # If passwords match and old password does also
            if temp_password == re_password and password == old_password:
                # See if exists in database and/or valid
                valid_password = evaluate_password(temp_password)
                password_exists = db.session.query(Users.id).filter_by(password=temp_password).first() is not None

                # Password already taken
                if password_exists:
                    return render_template("changepassword.html", old_wrong=False, no_match=False, invalid=False,
                                           taken=True)
                # Password invalid
                elif not valid_password:
                    return render_template("changepassword.html", old_wrong=False, no_match=False, invalid=True,
                                           taken=False)

                # Valid and unique password
                if not password_exists and valid_password:
                    try:
                        # Email to change
                        to_change = Users.query.filter_by(email=email).first()
                        to_change.password = temp_password

                        # Update password and commit
                        password = valid_password
                        db.session.commit()
                    except:
                        return render_template("changepassword.html", old_wrong=False, no_match=True, invalid=False,
                                               taken=False)

                    return redirect(url_for("load"))

            else:
                return render_template("changepassword.html", old_wrong=False, no_match=True, invalid=False,
                                       taken=False)

        return render_template("changepassword.html", old_wrong=False, no_match=False, invalid=False, taken=False)

    # If invalid fields, reload to main
    else:
        return redirect(url_for("load"))


def send_email(email, subject):
    # Global variables
    global two_step_code, email_code

    # Server to send email
    ctx = ssl.create_default_context()
    master_email = "thomaskahng1@gmail.com"
    master_password = "qgfojeeynyflvxtj"

    # Create the message
    message = MIMEMultipart("mixed")
    message["Subject"] = "Hello Mixed Multipart World!"
    message["From"] = master_email
    message["To"] = email

    message_content = ""
    if subject == "Signup":
        # Random signup verification code sent
        email_code = str(random.randint(100000, 1000000))
        message_content = f"Your email registration verification code is: {email_code}"

    elif subject == "Login":
        # Random login verification code sent
        two_step_code = str(random.randint(100000, 1000000))
        message_content = f"Your login verification code is: {two_step_code}"

    elif subject == "Recovery":
        # Information to recover password
        global username, password
        message_content = f"Your login information is:\n" \
                          f"Username: {username}\n" \
                          f"Password: {password}"

    # Attach message body content
    message.attach(MIMEText(message_content, "plain"))

    # Start server and send email
    with smtplib.SMTP_SSL("smtp.gmail.com", port=465, context=ctx) as server:
        server.login(master_email, master_password)
        server.sendmail(master_email, email, message.as_string())


def evaluate_password(password):
    # Numbers and special characters
    numbers = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
    special_chars = ['"', "'", '!', '#', '$', '%', '&', '(', ')', '*', '+', ',', '-', '.',
                     '/', ':', ';', '<', '=', '>', '?', '@', '[', ']', '^', '_', '`', '{',
                     '|', '}', '~']
    # Count of necessary characters in password
    num_cnt = 0
    upper_cnt = 0
    lower_cnt = 0
    special_cnt = 0

    for char in password:
        # Number is in password
        if char in numbers:
            num_cnt += 1

        # Special character is in password
        if char in special_chars:
            special_cnt += 1

        # Uppercase character is in password
        if char.isupper():
            upper_cnt += 1

        # Lowercase character is in password
        if char.islower():
            lower_cnt += 1

    # Password in between 8 and 20 characters
    if 8 <= len(password) <= 20:
        # Has at least one of each true, else false
        if num_cnt > 0 and upper_cnt > 0 and lower_cnt > 0 and special_cnt > 0:
            return True
        else:
            return False
    # Not valid length, so false
    else:
        return False


def get_route_map(start, end, score):
    to = toConnect()
    to.set_origin_end(start, end)
    to.create_csv_from_flow()
    to.inference_data()
    to.determine_avoid_bbox(score)
    map, route, zoom, box, heat_map = to.get_route()
    return map, route, zoom, box, heat_map


def reset():
    # Reset login global variables
    global two_step_code, login_attempted, granted_login
    two_step_code = None
    login_attempted = None
    granted_login = None

    # Reset signup global variables
    global email_code, signup_attempted, granted_signup
    email_code = None
    signup_attempted = None
    granted_signup = None

    # Reset database fields
    global username, password, email
    username = None
    password = None
    email = None


# Run main on localhost
if __name__ == "__main__":
    app.run(debug=True)
    app.run(host='localhost', debug=True)
