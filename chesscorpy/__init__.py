import random
import time
from sqlite3 import connect, Row
from flask import Flask, render_template, session, redirect, request
from flask_session import Session
from chesscorpy.helpers import error, login_required

app = Flask(__name__)

# Configure sessions
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Initialize global constants
USERNAME_MAX_LEN = 15
DEFAULT_RATING = 1000
MIN_RATING = 1
MAX_RATING = 3000
PUBLIC_USER_ID = 0
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
        rating = int(request.form.get("rating")) if request.form.get("rating").isdigit() else DEFAULT_RATING
        notifications = 0 if not request.form.get("notifications") else 1

        # Handle error checking
        # TODO: More error checking (ie valid email, email length, etc)
        if not username or username.lower() == "public":
            return error("Please provide a valid username.", 400)
        elif not password:
            return error("Please provide a password.", 400)
        elif not email:
            return error("Please provide an email address.", 400)
        elif len(username) > USERNAME_MAX_LEN:
            return error(f"Username cannot be greater than {USERNAME_MAX_LEN} characters.", 400)
        elif not (MIN_RATING <= int(rating) <= MAX_RATING):
            return error(f"Rating must be a number between {MIN_RATING} and {MAX_RATING}", 400)

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

        db.close()

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
    db = connect(DATABASE_FILE)
    db.row_factory = Row

    # Selects all games that the current user has not created themselves, which are challenging the public, and which
    # have rating requirements meeting the current user's rating.
    rows = db.execute("SELECT game_requests.id,game_requests.turn_day_limit,game_requests.color,"
                      "game_requests.timestamp,users.username,users.rating FROM game_requests JOIN users ON "
                      "game_requests.user_id=users.id WHERE opponent_id=? AND user_id!=? "
                      "AND (SELECT rating FROM users WHERE id=? LIMIT 1) BETWEEN min_rating AND max_rating",
                      [PUBLIC_USER_ID, session["user_id"], session["user_id"]]).fetchall()
    db.close()
    games = [dict(row) for row in rows]

    return render_template("lobby.html", games=games)


@app.route("/newgame", methods=["GET", "POST"])
@login_required
def newgame():
    if request.method == "POST":
        username = request.form.get("username").lower()
        color = request.form.get("color")
        turnlimit = None if not request.form.get("turnlimit").isdigit() else int(request.form.get("turnlimit"))
        minrating = None if not request.form.get("minrating").isdigit() else int(request.form.get("minrating"))
        maxrating = None if not request.form.get("maxrating").isdigit() else int(request.form.get("maxrating"))
        public = 0 if not request.form.get("public") else 1

        # Handle error checking
        if not username:
            return error("Please enter the name of the user you wish to challenge.", 400)
        elif not color:
            return error("Please select the color you wish to play.", 400)
        elif not turnlimit:
            return error("Please enter a turn limit in days.", 400)
        elif not minrating:
            return error("Please enter the minimum rating you wish for people to see your challenge.", 400)
        elif not maxrating:
            return error("Please enter the maximum rating you wish for people to see your challenge.", 400)
        elif color not in ("random", "white", "black"):
            return error("Please enter a valid color.", 400)
        elif turnlimit < 1:
            return error("Please enter a turn limit greater than 0.", 400)
        elif not (1 <= minrating <= 3000):
            return error("Please enter a minimum rating between 1 and 3000.", 400)
        elif not (1 <= maxrating <= 3000):
            return error("Please enter a maximum rating between 1 and 3000.", 400)
        elif minrating > maxrating:
            return error("Please enter a minimum rating that is less than or equal to the maximum rating.", 400)

        db = connect(DATABASE_FILE)
        db.row_factory = Row

        # Check that the user someone wants to challenge actually exists if this is not a challenge to the public.
        if username != "public":
            opponent_id = db.execute("SELECT id FROM users WHERE LOWER(username)=?", [username]).fetchone()

            if not opponent_id:
                return error("Please enter a valid user to challenge.", 400)

            opponent_id.keys()
            opponent_id = opponent_id["id"]

            # Don't let dingdongs challenge themselves.
            if opponent_id == session["user_id"]:
                return error("You cannot challenge yourself.", 400)
        else:
            opponent_id = 0

        # Now enter the challenge into the database.
        db.execute("INSERT INTO game_requests (user_id, opponent_id, turn_day_limit,"
                   "min_rating, max_rating, color, public) VALUES(?, ?, ?, ?, ?, ?, ?)",
                   [session["user_id"], opponent_id, turnlimit, minrating, maxrating, color, public])
        db.commit()
        db.close()

        return redirect("/lobby")
    else:
        return render_template("newgame.html")


@app.route("/start")
@login_required
def start():
    request_id = request.args.get("id")

    # Don't allow blank or invalid request IDs.
    if not request_id or not request_id.isdigit():
        return redirect("/")

    db = connect(DATABASE_FILE)
    cur = db.cursor()
    cur.row_factory = Row

    # Make sure game request exists.
    game_request = cur.execute("SELECT * FROM game_requests WHERE id=?", [request_id]).fetchone()
    if not game_request:
        return redirect("/")

    # Determine which player is which color.
    if game_request["color"] == "white":
        white_id = game_request["user_id"]
        black_id = session["user_id"]
    elif game_request["color"] == "black":
        white_id = session["user_id"]
        black_id = game_request["user_id"]
    else:
        # Assign colors randomly.
        random.seed(time.time())

        if random.randint(0, 1) == 1:
            white_id = game_request["user_id"]
            black_id = session["user_id"]
        else:
            white_id = session["user_id"]
            black_id = game_request["user_id"]

    # Create game based off data in the game request.
    game_request.keys()
    cur.execute("INSERT INTO games (player_white_id,player_black_id,turn_day_limit,public) VALUES(?,?,?,?)",
                [white_id, black_id, game_request["turn_day_limit"], game_request["public"]])
    game_id = cur.lastrowid

    # Delete game request from database.
    cur.execute("DELETE FROM game_requests WHERE id=?", [request_id])

    db.commit()
    db.close()

    # Jump to the newly created game.
    return redirect(f"/game?id={game_id}")


@app.route("/game")
@login_required
def game():
    game_id = request.args.get("id")

    # Select game where if it exists and the user is either a player in the game or the game is public.
    db = connect(DATABASE_FILE)
    game_data = db.execute("SELECT * FROM games WHERE id=? AND (player_white_id=? OR player_black_id=? OR public=1)",
                           [game_id, session["user_id"], session["user_id"]]).fetchone()

    # Error handling
    if not game_data:
        return redirect("/")

    db.close()

    return render_template("game.html")
