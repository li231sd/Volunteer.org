from datetime import datetime
from flask import Blueprint, render_template, request, session, redirect, jsonify
from db import db
import re
import textwrap
import smtplib
from email.mime.text import MIMEText
from config import Config
from ai_recommendations import AIRecommender

events_bp = Blueprint('events', __name__)

@events_bp.route("/")
def index():
    if "user_id" not in session:
        return redirect("/login")

    options = []

    now = datetime.now()
    formatted_date = now.strftime("%Y-%m-%dT%H:%M")

    approved_applications = db.execute("SELECT * FROM application_for_review WHERE id IN (SELECT application_id FROM applications_approved) AND date_reg_deadline > ?", (formatted_date,)).fetchall()

    for application in approved_applications:
        options.append(
            {
                "id": application[0],
                "title": application[16],
                "description": application[17],
            }
        )

    user_info = db.execute("SELECT * FROM ai_setup_info WHERE user_id = ?", (session["user_id"],)).fetchall()
    if not user_info:
        return redirect("/ai_rec_sys_model_volunteer_org_4")

    recommender = AIRecommender(options)
    user_input = f"I like to {user_info[0][1]}. I have skills in {user_info[0][2]}."
    recommendations = recommender.recommend(user_input)

    final_options = []

    for rec in recommendations:
        db_output = db.execute("SELECT * FROM application_for_review WHERE id = ?", (rec["id"],)).fetchone()
        final_options.append([
            db_output[16],
            db_output[6],
            textwrap.shorten(db_output[17], 94, placeholder="..."),
            round(rec["score"], 1)
        ])

    return render_template("index.html", options=final_options)

@events_bp.route("/find_more", methods=["GET"])
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

@events_bp.route("/rsvp", methods=["POST"])
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

@events_bp.route("/register-event", methods=["GET", "POST"])
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
                                   states_list=Config.STATES)

        if not email_organizer:
            return render_template("register_event.html", message="Organizer email is required!", show=True,
                                   states_list=Config.STATES)

        if not city_organizer:
            return render_template("register_event.html", message="Organizer city is required!", show=True,
                                   states_list=Config.STATES)

        if not state_organizer:
            return render_template("register_event.html", message="Organizer state is required!", show=True,
                                   states_list=Config.STATES)

        if not zip_organizer:
            return render_template("register_event.html", message="Organizer ZIP code is required!", show=True,
                                   states_list=Config.STATES)

        if not organization_name:
            return render_template("register_event.html", message="Organization name is required!", show=True,
                                   states_list=Config.STATES)

        if not organization_email:
            return render_template("register_event.html", message="Organization email is required!", show=True,
                                   states_list=Config.STATES)

        if not activity_age:
            return render_template("register_event.html", message="Activity age group is required!", show=True,
                                   states_list=Config.STATES)

        if not activity_city:
            return render_template("register_event.html", message="Activity city is required!", show=True,
                                   states_list=Config.STATES)

        if not activity_state:
            return render_template("register_event.html", message="Activity state is required!", show=True,
                                   states_list=Config.STATES)

        if not activity_zip:
            return render_template("register_event.html", message="Activity ZIP code is required!", show=True,
                                   states_list=Config.STATES)

        if not max_people:
            return render_template("register_event.html", message="Max people is required!", show=True,
                                   states_list=Config.STATES)

        if not date_start:
            return render_template("register_event.html", message="Start date is required!", show=True,
                                   states_list=Config.STATES)

        if not date_end:
            return render_template("register_event.html", message="End date is required!", show=True,
                                   states_list=Config.STATES)

        if not date_reg_deadline:
            return render_template("register_event.html", message="Registration deadline is required!", show=True,
                                   states_list=Config.STATES)
        if not activity_name:
            return render_template("register_event.html", message="Activity name is required!", show=True,
                                   states_list=Config.STATES)

        if not description:
            return render_template("register_event.html", message="Description is required!", show=True,
                                   states_list=Config.STATES)

        # Original code for email validation from geeksforgeeks
        email_organizer_valid = re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email_organizer)
        organization_email_valid = re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', organization_email)

        if not email_organizer_valid or not organization_email_valid:
            return render_template("register_event.html", message="Email format not valid!", show=True,
                                   states_list=Config.STATES)

        try:
            int(max_people)
        except ValueError:
            return render_template("register_event.html", message="Max people must be positive!", show=True,
                                   states_list=Config.STATES)
        try:
            int(activity_age)
        except ValueError:
            return render_template("register_event.html", message="Activity age must be positive!", show=True,
                                   states_list=Config.STATES)

        if int(max_people) <= 0:
            return render_template("register_event.html", message="Max people must be positive!", show=True,
                                   states_list=Config.STATES)
        if int(max_people) < 12:
            return render_template("register_event.html", message="Activity age must be at least 12!", show=True,
                                   states_list=Config.STATES)

        if date_start >= date_end:
            return render_template("register_event.html", message="Date start must be before date end!", show=True,
                                   states_list=Config.STATES)

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
                               states_list=Config.STATES)

@events_bp.route("/del_event_secure", methods=["POST"])
def del_event_secure():
    if "user_id" not in session:
        return redirect("/login")
    
    if request.method == "POST":
        data = request.get_json()
        application_id = int(data.get("id"))

        if not application_id:
            return redirect("/")

        event_bg_check = db.execute("SELECT id FROM application_for_review WHERE id = ? AND account_id = ?", (application_id, session["user_id"],))

        if not event_bg_check:
            return jsonify({"response": "Can't preform action!"}), 401

        sender_email = "donotreply.volunteer.org@gmail.com"
        app_password = "oqek ztdx cvdh vxhw" 

        to_email = []
        
        rsvp_people = db.execute("SELECT email FROM users WHERE id IN (SELECT user_id FROM rsvp WHERE application_id = ?)", (application_id,)).fetchall()

        for person in rsvp_people:
            to_email.append(person[0])

        msg_template = """
        Hello,

        Event #{application_id} has been canceled.

        On behalf of the organizer we apologize for any inconvenience this may cause. 
        If you have any questions, please contact the event organizer.

        Thank you,
        The Volunteer.org Team
        SAFETY IS OUR FIRST PRIORITY!
        
        """

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, app_password)
            for recipient in to_email:
                msg = MIMEText(msg_template.format(application_id=application_id), "plain")
                msg["Subject"] = f"Event #{application_id} Cancelled"
                msg["From"] = sender_email
                msg["To"] = recipient
                server.sendmail(sender_email, recipient, msg.as_string())
        
        db.execute("DELETE FROM rsvp WHERE application_id = ?", (application_id,)) 
        db.execute("DELETE FROM applications_approved WHERE application_id = ?", (application_id,)) 
        db.execute("DELETE FROM application_for_review WHERE id = ?", (application_id,))
       
        return jsonify({"success": True})
    else:
        return redirect("/")
    