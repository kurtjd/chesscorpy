from sqlite3 import connect, Row
from flask import Flask, render_template, session, redirect, request
from flask_session import Session
from chesscorpy.helpers import error, login_required

app = Flask(__name__)

# Configure sessions
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Setup globals
USERNAME_MAX_LEN = 15
DATABASE_FILE = "chesscorpy.db"


@app.route("/")
def index():
    # If user is already logged in, just redirect to the game lobby.
    if session.get("user_id") is not None:
        return redirect("/lobby")
    else:
        return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    # If user is logged in, just go back to home page.
    if session.get("user_id"):
        return redirect("/")

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        email = request.form.get("email")
        rating = int(request.form.get("rating")) if request.form.get("rating").isdigit() else 1000  # Default to 1000
        notifications = 0 if not request.form.get("notifications") else 1

        # Handle error checking
        # TODO: More error checking (ie valid email, email length, etc)
        if not username:
            return error("Please provide a username.", 400)
        elif not password:
            return error("Please provide a password.", 400)
        elif not email:
            return error("Please provide an email address.", 400)
        elif len(username) > USERNAME_MAX_LEN:
            return error(f"Username cannot be greater than {USERNAME_MAX_LEN} characters.", 400)
        elif not (1 <= int(rating) <= 3000):
            return error("Rating must be a number between 1 and 3000", 400)

        db = connect(DATABASE_FILE)
        db.row_factory = Row

        # Make sure username is not already taken
        if db.execute("SELECT username FROM users WHERE username=?", [username]).fetchone():
            return error("Username already exists", 400)

        # Finally create new user in database
        # TODO: Hash password
        db.execute("INSERT INTO users (username, password, email, rating, notifications) VALUES(?, ?, ?, ?, ?)",
                   [username, password, email, rating, notifications])

        # Auto login user
        user_id = db.execute("SELECT id FROM users WHERE username=?", [username]).fetchone()
        user_id.keys()
        session["user_id"] = user_id["id"]

        db.commit()
        db.close()

        return redirect("/lobby")
    else:
        return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username").lower()
        password = request.form.get("password")

        # Handle error checking
        # TODO: More error checking
        if not username:
            return error("Please provide a username.", 400)
        elif not password:
            return error("Please provide a password.", 400)

        # Attempt to login user
        db = connect(DATABASE_FILE)
        db.row_factory = Row
        user_id = db.execute("SELECT id FROM users WHERE LOWER(username)=? AND password=?",
                             [username, password]).fetchone()

        # Make sure username and password combination is valid.
        if not user_id:
            return error("Username and password combination is invalid.", 400)

        # If valid, create session with user's id
        user_id.keys()
        session["user_id"] = user_id["id"]

        return redirect("/lobby")
    else:
        return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    # Delete user's session and return to homepage.
    session.clear()
    return redirect("/")


@app.route("/lobby")
@login_required
def lobby():
    return render_template("lobby.html")
