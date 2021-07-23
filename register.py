from main import app
from flask import request, redirect, render_template
from sqlite3 import connect
from helpers import error
from globals import USERNAME_MAX_LEN, DATABASE_FILE


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Just to make things easier to read
        username = request.form.get("username")
        password = request.form.get("password")
        email = request.form.get("email")
        rating = request.form.get("rating")
        notifications = 0 if not request.form.get("notifications") else 1

        # Handle error checking
        # TODO: More error checking
        if not username:
            return error("Please provide a username.", 400)
        elif not password:
            return error("Please provide a password.", 400)
        elif not email:
            return error("Please provide an email address.", 400)
        elif len(username) > USERNAME_MAX_LEN:
            return error(f"Username cannot be greater than {USERNAME_MAX_LEN} characters.", 400)

        db = connect(DATABASE_FILE)

        # Make sure username is not already taken
        if db.execute("SELECT username FROM users WHERE username=?", [username]).fetchone():
            return error("Username already exists", 400)

        # Finally create new user in database
        db.execute("INSERT INTO users (username, password, email, rating, notifications) VALUES(?, ?, ?, ?, ?)",
                   [username, password, email, rating, notifications])

        db.commit()
        db.close()

        return redirect("/")
    else:
        return render_template("register.html")
