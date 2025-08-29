from datetime import datetime
from flask import Blueprint, render_template, session, redirect
from db import fetchall

user_bp = Blueprint('user', __name__)

@user_bp.route("/my_events", methods=["GET"])
def my_event():
    if "user_id" not in session:
        return redirect("/login")
    
    now = datetime.now()
    formatted_date = now.strftime("%Y-%m-%dT%H:%M")
    
    # Get events hosted by the user
    events_hosted = fetchall(
        """SELECT * FROM application_for_review 
        WHERE account_id = ? 
        AND id IN (SELECT application_id FROM applications_approved) 
        AND date_start > ?""", 
        (session["user_id"], formatted_date)
    )
    
    # Get attendees for each hosted event
    events_attendees = []
    for event in events_hosted:
        attendees = fetchall(
            "SELECT * FROM users WHERE id IN (SELECT user_id FROM rsvp WHERE application_id = ?)", 
            (event[0],)
        )
        for attendee in attendees:
            events_attendees.append([
                event[0],    # event id
                attendee     # attendee info
            ])

    return render_template("my_event.html", events_hosted=events_hosted, events_attendees=events_attendees)

@user_bp.route("/volunteer_history", methods=["GET"])
def volunteer_history():
    if "user_id" not in session:
        return redirect("/login")

    # Get events the user attended
    attended_events = fetchall("SELECT * FROM rsvp WHERE user_id = ?", (session["user_id"],))
    
    # Get events the user hosted
    hosted_events = fetchall(
        """SELECT * FROM application_for_review 
        WHERE account_id = ? 
        AND id IN (SELECT application_id FROM applications_approved)""", 
        (session["user_id"],)
    )

    events_attended = []
    events_hosted = []

    # Process attended events
    for event in attended_events:
        rows = fetchall("SELECT * FROM application_for_review WHERE id = ?", (event[1],))
        if rows:
            events_attended.append([
                event[1],      # application_id
                rows[0][6],    # organization_name
                rows[0][13],   # date_start
                rows[0][14]    # date_end
            ])

    # Process hosted events
    for event in hosted_events:
        rows = fetchall("SELECT * FROM applications_approved WHERE application_id = ?", (event[0],))
        events_hosted.append([
            event[0],      # application_id
            rows[0][0],    # approval_id
            event[16],     # activity_name
            rows[0][3],    # approval_date
            event[13],     # date_start
            event[14]      # date_end
        ])

    return render_template("volunteer_history.html", events_attended=events_attended, events_hosted=events_hosted)
