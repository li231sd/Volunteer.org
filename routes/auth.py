from flask import Blueprint, render_template, request, session, redirect
from werkzeug.security import check_password_hash, generate_password_hash
from db import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
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

@auth_bp.route("/register", methods=["GET", "POST"])
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

@auth_bp.route("/logout", methods=["GET"])
def logout():
    session.clear()
    return redirect("/login")
