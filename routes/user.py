from datetime import datetime
from flask import Blueprint, render_template, session, redirect
from db import db

user_bp = Blueprint('user', __name__)

@user_bp.route("/my_events", methods=["GET"])
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

@user_bp.route("/volunteer_history", methods=["GET"])
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
