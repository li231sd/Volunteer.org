from datetime import datetime
from flask import Blueprint, render_template, request, session, redirect, jsonify
from werkzeug.security import check_password_hash
from db import db

staff_bp = Blueprint('staff', __name__)

@staff_bp.route("/staff-login-secured", methods=["GET", "POST"])
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

@staff_bp.route("/logout-staff", methods=["GET"])
def staff_logout():
    session.clear()
    return redirect("/staff-login-secured")

@staff_bp.route("/review_applications", methods=["GET", "POST"])
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

@staff_bp.route("/review_self", methods=["GET"])
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
