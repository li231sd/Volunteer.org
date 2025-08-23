from crypt import methods
from datetime import datetime
from flask import Flask, flash, redirect, render_template, request, session, jsonify
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash


import smtplib
from email.mime.text import MIMEText

import re
import sqlite3
import textwrap

app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

conn = sqlite3.connect('volunteer.db', check_same_thread=False, isolation_level=None)
db = conn.cursor()

# Source: Stackoverflow
states = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DC", "DE", "FL", "GA", "HI", "ID", "IL", "IN", "IA", "KS", "KY",
          "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH",
          "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"]

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
def index():
    if "user_id" not in session:
        return redirect("/login")

    options = []

    now = datetime.now()
    formatted_date = now.strftime("%Y-%m-%dT%H:%M")

    approved_applications = db.execute("SELECT * FROM application_for_review WHERE id IN (SELECT application_id FROM applications_approved) AND date_reg_deadline > ?", (formatted_date,)).fetchall()

    for application in approved_applications:
        options.append([
            application[16],
            application[6],
            textwrap.shorten(application[17], 94, placeholder="..."),
            application[0]
        ])

    return render_template("index.html", options=options)

@app.route("/find_more", methods=["GET"])
def find_more():
    if "user_id" not in session:
        return redirect("/login")

    if request.method == "GET":
        application_id = request.args.get("id")

        if application_id is None:
            return redirect("/")

        info = db.execute("SELECT * FROM application_for_review WHERE id = ?", (application_id,)).fetchall()
        return render_template("find_more.html", info=info)

    else:
        return redirect("/")

@app.route("/rsvp", methods=["POST"])
def rsvp():
    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":
        data = request.get_json()
        application_id = int(data.get("id"))

        if application_id is None:
            return jsonify({"response": "Something went wrong!"}), 401

        is_user_in_event = db.execute("SELECT id FROM rsvp WHERE application_id = ? AND user_id = ?", (application_id, session["user_id"]),).fetchone()
        if is_user_in_event:
            return jsonify({"response": "Something went wrong!"}), 401

        who_own_event = db.execute("SELECT * FROM application_for_review WHERE id = ?", (application_id,)).fetchall()
        if who_own_event[0][18] == int(session["user_id"]):
            return jsonify({"response": "Something went wrong!"}), 401

        db.execute("INSERT INTO rsvp (application_id, user_id) VALUES (?, ?)", (application_id, session["user_id"]))

        sender_email = "donotreply.volunteer.org@gmail.com"
        app_password = "oqek ztdx cvdh vxhw" 

        to_email = db.execute("SELECT email FROM users WHERE id = ?", (session["user_id"],)).fetchone()[0]

        msg = MIMEText(f"Thanks for RSVPing to event #{application_id}! We will see you there!")
        msg["Subject"] = "RSVP Confirmation"
        msg["From"] = sender_email
        msg["To"] = to_email

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, app_password)
            server.sendmail(sender_email, to_email, msg.as_string())


        organizer_email = db.execute("SELECT email FROM users WHERE id = ?", (who_own_event[0][18],)).fetchone()[0]
        username = db.execute("SELECT username FROM users WHERE id = ?", (session["user_id"],)).fetchone()[0]

        msg = MIMEText(
            f"""
            Hello,

            User **{username}** has registered for **Event #{application_id}**.

            You can review their information on the website. As the organizer, you may:
            - Approve or deny their registration
            - Provide them with additional details through the website or by email

            Please log in to the website to manage this registration.

            Thank you,
            The Volunteer.org Team
            """,
            "plain"
        )

        msg["Subject"] = "RSVP Confirmation"
        msg["From"] = sender_email
        msg["To"] = organizer_email

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, app_password)
            server.sendmail(sender_email, organizer_email, msg.as_string())

        return jsonify({"success": True})

    return jsonify({"response": "Something went wrong!"}), 401

@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            return render_template("login.html", message="One or more fields were left blank!", show=True)

        rows = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchall()
        if not rows:
            return render_template("login.html", message="We can't find you!", show=True)

        if not check_password_hash(rows[0][5], password):
            return render_template("login.html", message="Incorrect password!", show=True)

        session["user_id"] = rows[0][0]
        return redirect("/")
    else:
        return render_template("login.html", message="If you can see this that means I did something wrong!",
                               show=False)

@app.route("/my_events", methods=["GET"])
def my_event():
    if "user_id" not in session:
        return redirect("/login")
    
    now = datetime.now()
    formatted_date = now.strftime("%Y-%m-%dT%H:%M")
    
    events_hosted = db.execute("SELECT * FROM application_for_review WHERE account_id = ? AND id IN (SELECT application_id FROM applications_approved) AND date_start > ?", (session["user_id"],formatted_date,)).fetchall()
    
    events_attendees = []
    for event in events_hosted:
        attendees = db.execute("SELECT * FROM users WHERE id IN (SELECT user_id FROM rsvp WHERE application_id = ?)", (event[0],))
        for attendee in attendees:
            events_attendees.append(
                [
                    event[0],
                    attendee
                ]
            )

    return render_template("my_event.html", events_hosted=events_hosted, events_attendees=events_attendees)

@app.route("/del_event_secure", methods=["POST"])
def del_event_secure():
    if "user_id" not in session:
        return redirect("/login")
    
    if request.method == "POST":
        data = request.get_json()
        application_id = int(data.get("id"))
        
    else:
        return redirect("/")

@app.route("/volunteer_history", methods=["GET"])
def volunteer_history():
    if "user_id" not in session:
        return redirect("/login")

    attended_events = db.execute("SELECT * FROM rsvp WHERE user_id = ?", (session["user_id"],)).fetchall()
    hosted_events = db.execute("SELECT * FROM application_for_review WHERE account_id = ? AND id IN (SELECT application_id FROM applications_approved)", (session["user_id"],)).fetchall()

    events_attended = []
    events_hosted = []

    for event in attended_events:
        rows = db.execute("SELECT * FROM application_for_review WHERE id = ?", (event[1],)).fetchone()
        if rows:
            events_attended.append(
                [
                    event[1],
                    rows[6],
                    rows[13],
                    rows[14]
                ]
            )

    for event in hosted_events:
        rows = db.execute("SELECT * FROM applications_approved WHERE application_id = ?", (event[0],)).fetchall()

        events_hosted.append(
            [
                event[0],
                rows[0][0],
                event[16],
                rows[0][3],
                event[13],
                event[14]
            ]
        )

    return render_template("volunteer_history.html", events_attended=events_attended, events_hosted=events_hosted)

@app.route("/register", methods=["GET", "POST"])
def register():
    session.clear()

    if request.method == "POST":
        # Get all values
        name = request.form.get("legal-name")
        email = request.form.get("email")
        age = request.form.get("age")
        username = request.form.get("username")
        password = request.form.get("password")

        # Make sure all fields were filled
        if not name or not email or not age or not username or not password:
            return render_template("register.html", message="One or more fields were left blank!", show=True)

        # Make sure they are the correct age
        if int(age) <= 11:
            return render_template("register.html", message="Must be at least 12 years old!", show=True)

        # Make sure age is a number
        try:
            int(age)
        except ValueError:
            return render_template("register.html", message="Age must be a number!", show=True)

        # Make sure there is nobody with the same username
        usernames = db.execute("SELECT username FROM users WHERE username = ?", (username,)).fetchall()
        if len(usernames) != 0:
            return render_template("register.html", message="Username already taken!", show=True)

        db.execute(
            "INSERT INTO users ('name', 'email', 'age', 'username', 'password') VALUES (?, ?, ?, ?, ?)",
            (name, email, age, username, generate_password_hash(password))
        )

        id_finder = db.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchall()

        session["user_id"] = id_finder[0][0]

        return redirect("/")

    else:
        return render_template("register.html", message="If you can see this that means I did something wrong!",
                               show=False)

@app.route("/logout", methods=["GET"])
def logout():
    session.clear()
    return redirect("/login")

@app.route("/logout-staff", methods=["GET"])
def staff_logout():
    session.clear()
    return redirect("/staff-login-secured")


@app.route("/register-event", methods=["GET", "POST"])
def register_event():
    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":
        name_organizer = request.form.get("name-organizer")
        email_organizer = request.form.get("email-organizer")
        city_organizer = request.form.get("city-organizer")
        state_organizer = request.form.get("state-organizer")
        zip_organizer = request.form.get("zip-organizer")

        organization_name = request.form.get("organization-name")
        organization_email = request.form.get("organization-email")

        activity_age = request.form.get("activity-age")
        activity_city = request.form.get("activity-city")
        activity_state = request.form.get("activity-state")
        activity_zip = request.form.get("activity-zip")

        max_people = request.form.get("max-people")

        date_start = request.form.get("date-start")
        date_end = request.form.get("date-end")
        date_reg_deadline = request.form.get("date-reg-deadline")

        activity_name = request.form.get("activity-name")
        description = request.form.get("description")

        rules = request.form.get("rules")

        if not name_organizer:
            return render_template("register_event.html", message="Organizer name is required!", show=True,
                                   states_list=states)

        if not email_organizer:
            return render_template("register_event.html", message="Organizer email is required!", show=True,
                                   states_list=states)

        if not city_organizer:
            return render_template("register_event.html", message="Organizer city is required!", show=True,
                                   states_list=states)

        if not state_organizer:
            return render_template("register_event.html", message="Organizer state is required!", show=True,
                                   states_list=states)

        if not zip_organizer:
            return render_template("register_event.html", message="Organizer ZIP code is required!", show=True,
                                   states_list=states)

        if not organization_name:
            return render_template("register_event.html", message="Organization name is required!", show=True,
                                   states_list=states)

        if not organization_email:
            return render_template("register_event.html", message="Organization email is required!", show=True,
                                   states_list=states)

        if not activity_age:
            return render_template("register_event.html", message="Activity age group is required!", show=True,
                                   states_list=states)

        if not activity_city:
            return render_template("register_event.html", message="Activity city is required!", show=True,
                                   states_list=states)

        if not activity_state:
            return render_template("register_event.html", message="Activity state is required!", show=True,
                                   states_list=states)

        if not activity_zip:
            return render_template("register_event.html", message="Activity ZIP code is required!", show=True,
                                   states_list=states)

        if not max_people:
            return render_template("register_event.html", message="Max people is required!", show=True,
                                   states_list=states)

        if not date_start:
            return render_template("register_event.html", message="Start date is required!", show=True,
                                   states_list=states)

        if not date_end:
            return render_template("register_event.html", message="End date is required!", show=True,
                                   states_list=states)

        if not date_reg_deadline:
            return render_template("register_event.html", message="Registration deadline is required!", show=True,
                                   states_list=states)
        if not activity_name:
            return render_template("register_event.html", message="Activity name is required!", show=True,
                                   states_list=states)

        if not description:
            return render_template("register_event.html", message="Description is required!", show=True,
                                   states_list=states)

        # Original code for email validation from geeksforgeeks
        email_organizer_valid = re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email_organizer)
        organization_email_valid = re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', organization_email)

        if not email_organizer_valid or not organization_email_valid:
            return render_template("register_event.html", message="Email format not valid!", show=True,
                                   states_list=states)

        try:
            int(max_people)
        except ValueError:
            return render_template("register_event.html", message="Max people must be positive!", show=True,
                                   states_list=states)
        try:
            int(activity_age)
        except ValueError:
            return render_template("register_event.html", message="Activity age must be positive!", show=True,
                                   states_list=states)

        if int(max_people) <= 0:
            return render_template("register_event.html", message="Max people must be positive!", show=True,
                                   states_list=states)
        if int(max_people) < 12:
            return render_template("register_event.html", message="Activity age must be at least 12!", show=True,
                                   states_list=states)

        if date_start >= date_end:
            return render_template("register_event.html", message="Date start must be before date end!", show=True,
                                   states_list=states)

        account_info = db.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],)).fetchall()

        db.execute(
            "INSERT INTO application_for_review (name_organizer, email_organizer, city_organizer, state_organizer, zip_organizer, organization_name, organization_email, activity_age, activity_city, activity_state, activity_zip, max_people, date_start, date_end, date_reg_deadline, activity_name, description, account_id, account_name, account_email, account_user_age, account_username) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (name_organizer, email_organizer, city_organizer, state_organizer, zip_organizer, organization_name,
             organization_email, activity_age, activity_city, activity_state, activity_zip, max_people, date_start,
             date_end, date_reg_deadline, activity_name, description, session["user_id"], account_info[0][1], account_info[0][2], account_info[0][3], account_info[0][4])
        )

        return redirect("/")
    else:
        return render_template("register_event.html", message="You should not be able to see this!", show=False,
                               states_list=states)


@app.route("/staff-login-secured", methods=["GET", "POST"])
def staff_login_secured():
    session.clear()

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            return render_template("staff_login.html", message="One or more fields were left blank!", show=True)

        rows = db.execute("SELECT * FROM staff WHERE username = ?", (username,)).fetchall()
        if not rows:
            return render_template("staff_login.html", message="We can't find you!", show=True)

        if not check_password_hash(rows[0][2], password):
            return render_template("staff_login.html", message="Incorrect password!", show=True)

        session["staff_id"] = rows[0][0]
        return redirect("/review_applications")

    else:
        return render_template("staff_login.html", message="You should not be able to see this!", show=False,)

@app.route("/review_applications", methods=["GET", "POST"])
def review_applications():
    if "staff_id" not in session:
        return redirect("/staff-login-secured")

    if request.method == "POST":
        data = request.get_json()
        application_id = data.get("id")
        approved = data.get("approve")

        now = datetime.now()
        formatted_date = now.strftime("%Y-%m-%dT%H:%M")

        if int(approved) == 1:
            db.execute("INSERT INTO applications_approved (application_id, staff_id, date) VALUES (?, ?, ?)", (application_id, session["staff_id"], formatted_date))
            return jsonify({"success": True})
        else:
            db.execute("INSERT INTO applications_denied (application_id, staff_id, date) VALUES (?, ?, ?)", (application_id, session["staff_id"], formatted_date))
            return jsonify({"success": True})

    else:
        show_no_reviews = False
        rows = db.execute("SELECT * FROM application_for_review WHERE id NOT IN (SELECT application_id FROM applications_approved) AND id NOT IN (SELECT application_id FROM applications_denied)").fetchall()
        if len(rows) == 0:
            show_no_reviews = True
        return render_template("review_applications.html", message="You should not be able to see this!", show=False, rows=rows, show_no_reviews=show_no_reviews)

@app.route("/review_self", methods=["GET"])
def review_self():
    if "staff_id" not in session:
        return redirect("/staff-login-secured")

    history_approved = []
    rows_approved = db.execute("SELECT * FROM applications_approved WHERE staff_id = ?", (session["staff_id"],)).fetchall()
    for row in rows_approved:
        application = db.execute("SELECT * FROM application_for_review WHERE id = ?", (row[0],)).fetchall()
        if application:
            history_approved.append(
                [
                    row[1],
                    row[0],
                    application[0][18],
                    row[3]
                ]
            )

    history_denied = []
    rows_denied = db.execute("SELECT * FROM applications_denied WHERE staff_id = ?", (session["staff_id"],)).fetchall()
    for row in rows_denied:
        application = db.execute("SELECT * FROM application_for_review WHERE id = ?", (row[0],)).fetchall()
        if application:
            history_denied.append(
                [
                    row[1],
                    row[0],
                    application[0][18],
                    row[3]
                ]
            )

    return render_template("staff_history.html", history_approved=history_approved, history_denied=history_denied)
