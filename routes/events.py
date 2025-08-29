import re
import textwrap
from datetime import datetime
from flask import Blueprint, render_template, request, session, redirect, jsonify
from db import execute_query, fetchall, fetchone
from email_utils import send_rsvp_confirmation, send_organizer_notification, send_event_cancellation
from config import Config

events_bp = Blueprint('events', __name__)

@events_bp.route("/")
def index():
    if "user_id" not in session:
        return redirect("/login")

    options = []
    now = datetime.now()
    formatted_date = now.strftime("%Y-%m-%dT%H:%M")

    approved_applications = fetchall(
        "SELECT * FROM application_for_review WHERE id IN (SELECT application_id FROM applications_approved) AND date_reg_deadline > ?", 
        (formatted_date,)
    )

    for application in approved_applications:
        options.append([
            application[16],
            application[6],
            textwrap.shorten(application[17], 94, placeholder="..."),
            application[0]
        ])

    return render_template("index.html", options=options)

@events_bp.route("/find_more", methods=["GET"])
def find_more():
    if "user_id" not in session:
        return redirect("/login")

    if request.method == "GET":
        application_id = request.args.get("id")

        if application_id is None:
            return redirect("/")

        info = fetchall("SELECT * FROM application_for_review WHERE id = ?", (application_id,))
        return render_template("find_more.html", info=info)

    else:
        return redirect("/")

@events_bp.route("/rsvp", methods=["POST"])
def rsvp():
    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":
        data = request.get_json()
        application_id = int(data.get("id"))

        if application_id is None:
            return jsonify({"response": "Something went wrong!"}), 401

        is_user_in_event = fetchone(
            "SELECT id FROM rsvp WHERE application_id = ? AND user_id = ?", 
            (application_id, session["user_id"])
        )
        if is_user_in_event:
            return jsonify({"response": "Something went wrong!"}), 401

        who_own_event = fetchall("SELECT * FROM application_for_review WHERE id = ?", (application_id,))
        if who_own_event[0][18] == int(session["user_id"]):
            return jsonify({"response": "Something went wrong!"}), 401

        execute_query("INSERT INTO rsvp (application_id, user_id) VALUES (?, ?)", (application_id, session["user_id"]))

        # Send confirmation email to user
        to_email = fetchone("SELECT email FROM users WHERE id = ?", (session["user_id"],))[0]
        send_rsvp_confirmation(to_email, application_id)

        # Send notification email to organizer
        organizer_email = fetchone("SELECT email FROM users WHERE id = ?", (who_own_event[0][18],))[0]
        username = fetchone("SELECT username FROM users WHERE id = ?", (session["user_id"],))[0]
        send_organizer_notification(organizer_email, username, application_id)

        return jsonify({"success": True})

    return jsonify({"response": "Something went wrong!"}), 401

@events_bp.route("/register-event", methods=["GET", "POST"])
def register_event():
    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":
        # Get all form data
        form_data = {
            'name_organizer': request.form.get("name-organizer"),
            'email_organizer': request.form.get("email-organizer"),
            'city_organizer': request.form.get("city-organizer"),
            'state_organizer': request.form.get("state-organizer"),
            'zip_organizer': request.form.get("zip-organizer"),
            'organization_name': request.form.get("organization-name"),
            'organization_email': request.form.get("organization-email"),
            'activity_age': request.form.get("activity-age"),
            'activity_city': request.form.get("activity-city"),
            'activity_state': request.form.get("activity-state"),
            'activity_zip': request.form.get("activity-zip"),
            'max_people': request.form.get("max-people"),
            'date_start': request.form.get("date-start"),
            'date_end': request.form.get("date-end"),
            'date_reg_deadline': request.form.get("date-reg-deadline"),
            'activity_name': request.form.get("activity-name"),
            'description': request.form.get("description"),
            'rules': request.form.get("rules")
        }

        # Validation
        required_fields = [
            ('name_organizer', 'Organizer name is required!'),
            ('email_organizer', 'Organizer email is required!'),
            ('city_organizer', 'Organizer city is required!'),
            ('state_organizer', 'Organizer state is required!'),
            ('zip_organizer', 'Organizer ZIP code is required!'),
            ('organization_name', 'Organization name is required!'),
            ('organization_email', 'Organization email is required!'),
            ('activity_age', 'Activity age group is required!'),
            ('activity_city', 'Activity city is required!'),
            ('activity_state', 'Activity state is required!'),
            ('activity_zip', 'Activity ZIP code is required!'),
            ('max_people', 'Max people is required!'),
            ('date_start', 'Start date is required!'),
            ('date_end', 'End date is required!'),
            ('date_reg_deadline', 'Registration deadline is required!'),
            ('activity_name', 'Activity name is required!'),
            ('description', 'Description is required!')
        ]

        for field, error_msg in required_fields:
            if not form_data[field]:
                return render_template("register_event.html", message=error_msg, show=True, states_list=Config.STATES)

        # Email validation
        email_organizer_valid = re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', form_data['email_organizer'])
        organization_email_valid = re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', form_data['organization_email'])

        if not email_organizer_valid or not organization_email_valid:
            return render_template("register_event.html", message="Email format not valid!", show=True, states_list=Config.STATES)

        # Numeric validation
        try:
            max_people = int(form_data['max_people'])
            activity_age = int(form_data['activity_age'])
        except ValueError:
            return render_template("register_event.html", message="Max people and activity age must be numbers!", show=True, states_list=Config.STATES)

        if max_people <= 0:
            return render_template("register_event.html", message="Max people must be positive!", show=True, states_list=Config.STATES)
        
        if activity_age < 12:
            return render_template("register_event.html", message="Activity age must be at least 12!", show=True, states_list=Config.STATES)

        # Date validation
        if form_data['date_start'] >= form_data['date_end']:
            return render_template("register_event.html", message="Date start must be before date end!", show=True, states_list=Config.STATES)

        # Get account info
        account_info = fetchall("SELECT * FROM users WHERE id = ?", (session["user_id"],))

        # Insert into database
        execute_query(
            """INSERT INTO application_for_review 
            (name_organizer, email_organizer, city_organizer, state_organizer, zip_organizer, organization_name, 
            organization_email, activity_age, activity_city, activity_state, activity_zip, max_people, date_start, 
            date_end, date_reg_deadline, activity_name, description, account_id, account_name, account_email, 
            account_user_age, account_username) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (form_data['name_organizer'], form_data['email_organizer'], form_data['city_organizer'], 
             form_data['state_organizer'], form_data['zip_organizer'], form_data['organization_name'],
             form_data['organization_email'], activity_age, form_data['activity_city'], 
             form_data['activity_state'], form_data['activity_zip'], max_people, form_data['date_start'],
             form_data['date_end'], form_data['date_reg_deadline'], form_data['activity_name'], 
             form_data['description'], session["user_id"], account_info[0][1], account_info[0][2], 
             account_info[0][3], account_info[0][4])
        )

        return redirect("/")
    else:
        return render_template("register_event.html", message="You should not be able to see this!", 
                               show=False, states_list=Config.STATES)

@events_bp.route("/del_event_secure", methods=["POST"])
def del_event_secure():
    if "user_id" not in session:
        return redirect("/login")
    
    if request.method == "POST":
        data = request.get_json()
        application_id = int(data.get("id"))

        if not application_id:
            return redirect("/")

        event_bg_check = fetchone(
            "SELECT id FROM application_for_review WHERE id = ? AND account_id = ?", 
            (application_id, session["user_id"])
        )

        if not event_bg_check:
            return jsonify({"response": "Can't perform action!"}), 401

        # Get emails of people who RSVP'd
        rsvp_people = fetchall(
            "SELECT email FROM users WHERE id IN (SELECT user_id FROM rsvp WHERE application_id = ?)", 
            (application_id,)
        )
        to_email_list = [person[0] for person in rsvp_people]

        # Send cancellation emails
        send_event_cancellation(to_email_list, application_id)
        
        # Delete from database
        execute_query("DELETE FROM rsvp WHERE application_id = ?", (application_id,))
        execute_query("DELETE FROM applications_approved WHERE application_id = ?", (application_id,))
        execute_query("DELETE FROM application_for_review WHERE id = ?", (application_id,))
       
        return jsonify({"success": True})
    else:
        return redirect("/")
    