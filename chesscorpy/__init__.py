import random
import datetime
from sqlite3 import connect, Row
from flask import Flask, render_template, session, redirect, request
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from .helpers import error, login_required, player_colors
import chesscorpy.constants

app = Flask(__name__)

# Configure sessions
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


@app.route("/")
def index():
    """ Displays the homepage if user is not logged in, otherwise redirects them to the lobby. """

    # If user is already logged in, render different page.
    if session.get(constants.USER_SESSION) is not None:
        db = connect(constants.DATABASE_FILE)
        db.row_factory = Row
        user_data = db.execute("SELECT * FROM users WHERE id=?", [session[constants.USER_SESSION]]).fetchone()
        user_data.keys()
        db.close()

        return render_template("/index_loggedin.html", user_data=user_data)
    else:
        return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """ Allows a new user to register. """

    # If user is logged in, just go back to home page.
    if session.get(constants.USER_SESSION):
        return redirect("/")

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        email = request.form.get("email")
        rating = int(request.form.get("rating")) if request.form.get("rating").isdigit() else constants.DEFAULT_RATING
        notifications = 0 if not request.form.get("notifications") else 1

        # Handle error checking
        # TODO: More error checking (ie valid email, email length, etc)
        if not username or username.lower() == "public":
            return error("Please provide a valid username.", 400)
        elif not password:
            return error("Please provide a password.", 400)
        elif not email:
            return error("Please provide an email address.", 400)
        elif len(username) > constants.USERNAME_MAX_LEN:
            return error(f"Username cannot be greater than {constants.USERNAME_MAX_LEN} characters.", 400)
        elif not (constants.MIN_RATING <= int(rating) <= constants.MAX_RATING):
            return error(f"Rating must be a number between {constants.MIN_RATING} and {constants.MAX_RATING}", 400)

        db = connect(constants.DATABASE_FILE)
        db.row_factory = Row

        # Make sure username is not already taken
        if db.execute("SELECT username FROM users WHERE username=?", [username]).fetchone():
            return error("Username already exists", 400)

        # Finally create new user in database
        db.execute("INSERT INTO users (username,password,email,rating,notifications) VALUES(?,?,?,?,?)",
                   [username, generate_password_hash(password), email, rating, notifications])

        # Auto login user
        user_id = db.execute("SELECT id FROM users WHERE username=?", [username]).fetchone()
        user_id.keys()
        session[constants.USER_SESSION] = user_id["id"]

        db.commit()
        db.close()

        return redirect("/")
    else:
        return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """ Allows a user to login. """

    # If user is logged in, just go back to home page.
    if session.get(constants.USER_SESSION):
        return redirect("/")

    if request.method == "POST":
        username = request.form.get("username").lower()
        password = request.form.get("password")

        # Handle error checking
        if not username:
            return error("Please provide a username.", 400)
        elif not password:
            return error("Please provide a password.", 400)

        db = connect(constants.DATABASE_FILE)
        db.row_factory = Row

        # Retrieve user data by username.
        user = db.execute("SELECT id,username,password FROM users WHERE LOWER(username)=?",
                          [username]).fetchone()

        # Make sure username exists.
        if not user:
            return error("User does not exist.", 400)

        user.keys()

        # Make sure username and password combination is valid.
        if not check_password_hash(user["password"], password):
            return error("Username and password combination is invalid.", 400)

        # If valid, create session with user's id
        session[constants.USER_SESSION] = user["id"]

        db.close()

        return redirect("/")
    else:
        return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    """ Logs a user out. """

    # Delete user's session and return to homepage.
    session.clear()
    return redirect("/")


@app.route("/opengames")
@login_required
def opengames():
    """ Displays a list of public or private game requests and allows users to sort and accept these requests. """

    direct = request.args.get("direct")

    db = connect(constants.DATABASE_FILE)
    db.row_factory = Row

    if not direct:
        # Selects all games that the current user has not created themselves, which are challenging the public,
        # and which have rating requirements meeting the current user's rating.
        rows = db.execute("SELECT game_requests.id,game_requests.turn_day_limit,game_requests.color,"
                          "game_requests.timestamp,users.username,users.rating FROM game_requests JOIN users ON "
                          "game_requests.user_id=users.id WHERE opponent_id=? AND user_id!=? "
                          "AND (SELECT rating FROM users WHERE id=? LIMIT 1) BETWEEN min_rating AND max_rating",
                          [constants.PUBLIC_USER_ID, session[constants.USER_SESSION],
                           session[constants.USER_SESSION]]).fetchall()
    else:
        # Selects all games that are direct requests to the user.
        rows = db.execute("SELECT game_requests.id,game_requests.turn_day_limit,game_requests.color,"
                          "game_requests.timestamp,users.username,users.rating FROM game_requests JOIN users ON "
                          "game_requests.user_id=users.id WHERE opponent_id=?",
                          [session[constants.USER_SESSION]]).fetchall()
    db.close()
    games_ = [dict(row) for row in rows]

    return render_template("opengames.html", games=games_)


@app.route("/newgame", methods=["GET", "POST"])
@login_required
def newgame():
    """ Allows users to create a game request. """

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

        db = connect(constants.DATABASE_FILE)
        db.row_factory = Row

        # Check that the user someone wants to challenge actually exists if this is not a challenge to the public.
        if username != "public":
            opponent_id = db.execute("SELECT id FROM users WHERE LOWER(username)=?", [username]).fetchone()

            if not opponent_id:
                return error("Please enter a valid user to challenge.", 400)

            opponent_id.keys()
            opponent_id = opponent_id["id"]

            # Don't let dingdongs challenge themselves.
            if opponent_id == session[constants.USER_SESSION]:
                return error("You cannot challenge yourself.", 400)
        else:
            opponent_id = 0

        # Now enter the challenge into the database.
        db.execute("INSERT INTO game_requests (user_id,opponent_id,turn_day_limit,min_rating,max_rating,color,public)"
                   " VALUES(?,?,?,?,?,?,?)",
                   [session[constants.USER_SESSION], opponent_id, turnlimit, minrating, maxrating, color, public])
        db.commit()
        db.close()

        return redirect("/opengames")
    else:
        return render_template("newgame.html")


@app.route("/start")
@login_required
def start():
    """ Creates a game from a game request. """

    request_id = request.args.get("id")

    # Don't allow blank or invalid request IDs.
    if not request_id or not request_id.isdigit():
        return redirect("/")

    db = connect(constants.DATABASE_FILE)
    cur = db.cursor()
    cur.row_factory = Row

    # Make sure game request exists and that user is authorized to accept the request.
    game_request = cur.execute("SELECT * FROM game_requests WHERE id=? AND (opponent_id=0 OR opponent_id=?)",
                               [request_id, session[constants.USER_SESSION]]).fetchone()
    if not game_request:
        return redirect("/")

    # Determine which player is which color.
    if game_request["color"] == "white":
        white_id = game_request["user_id"]
        black_id = session[constants.USER_SESSION]
    elif game_request["color"] == "black":
        white_id = session[constants.USER_SESSION]
        black_id = game_request["user_id"]
    else:
        # Assign colors randomly.
        random.seed(datetime.datetime.now().timestamp())

        if random.randint(0, 1) == 1:
            white_id = game_request["user_id"]
            black_id = session[constants.USER_SESSION]
        else:
            white_id = session[constants.USER_SESSION]
            black_id = game_request["user_id"]

    # Create game based off data in the game request.
    game_request.keys()
    cur.execute("INSERT INTO games (player_white_id,player_black_id,turn_day_limit,to_move,public) VALUES(?,?,?,?,?)",
                [white_id, black_id, game_request["turn_day_limit"], white_id, game_request["public"]])
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
    """ Generates a game board based on the status of the game and allows user to make moves. """

    game_id = request.args.get("id")

    # Select game if it exists and the user is either a player in the game or the game is public.
    db = connect(constants.DATABASE_FILE)
    db.row_factory = Row
    game_data = db.execute("SELECT * FROM games WHERE id=? AND (player_white_id=? OR player_black_id=? OR public=1)",
                           [game_id, session[constants.USER_SESSION], session[constants.USER_SESSION]]).fetchone()

    # Error handling
    if not game_data:
        return redirect("/")

    game_data.keys()
    db.close()

    return render_template("game.html", game_data=game_data)


@app.route("/mygames")
@login_required
def mygames():
    """ Displays the active games of the user. """

    my_move = request.args.get("my_move")
    db = connect(constants.DATABASE_FILE)
    db.row_factory = Row

    # Either display all active games or only games where it's the user's turn to move.
    if my_move:
        games_ = db.execute("SELECT * FROM games WHERE to_move=? AND (status='no_move' OR status='in_progress')",
                            [session[constants.USER_SESSION]]).fetchall()
    else:
        games_ = db.execute("SELECT * FROM games WHERE player_white_id=? OR player_black_id=? AND "
                            "(status='no_move' OR status='in_progress')",
                            [session[constants.USER_SESSION], session[constants.USER_SESSION]]).fetchall()
    games_ = [dict(game_) for game_ in games_]

    # Add extra keys into games list for opponent info and user's color.
    # Might be able to simplify this with a fancier SQL statement, but it works fine for now.
    for game_ in games_:
        # Determine's user's and opponent's colors in game.
        game_["my_color"], opponent_color = player_colors(game_["player_white_id"], session[constants.USER_SESSION])

        # Retrieve info about the opponent and determine name of the player who's next to move.
        opponent = db.execute("SELECT id,username FROM users WHERE id=?",
                              [game_[f"player_{opponent_color}_id"]]).fetchone()
        opponent.keys()
        game_["opponent_name"] = opponent["username"]
        game_["opponent_id"] = opponent["id"]
        game_["player_to_move"] = db.execute("SELECT username FROM users WHERE id=?", [game_["to_move"]]).fetchone()[0]

        # Determines how much time left for the player who's turn it is to move.
        # Works by getting the time the move started, adds the turn limit to that time,
        # and then subtracts the current time from the total.
        game_["time_to_move"] = (datetime.datetime.strptime(game_["move_start_time"], "%Y-%m-%d %H:%M:%S") +
                                 (datetime.timedelta(days=game_["turn_day_limit"])) -
                                 datetime.datetime.now().replace(microsecond=0))

    db.close()
    return render_template("mygames.html", games=games_)


@app.route("/history")
@login_required
def history():
    """ Displays the game history of a user. """

    user_id = request.args.get("id")
    db = connect(constants.DATABASE_FILE)
    db.row_factory = Row

    # Check that the user exists and gets its username.
    user = db.execute("SELECT username FROM users WHERE id=?", [user_id]).fetchone()
    if not user:
        return error("That user does not exist.", 400)
    username = user[0]

    # Select completed games from the given user which are either
    # publically viewable or were played by the logged-in user.
    games_ = db.execute("SELECT * FROM games WHERE (public=1 OR player_white_id=? OR player_black_id=?) AND "
                        "(player_white_id=? OR player_black_id=?) AND status != 'no_move' AND status != 'in_progress'",
                        [session[constants.USER_SESSION], session[constants.USER_SESSION], user_id, user_id]).fetchall()
    games_ = [dict(game_) for game_ in games_]

    for game_ in games_:
        # Get the names of the players.
        game_["player_white_name"] = db.execute("SELECT username FROM users WHERE id=?",
                                                [game_["player_white_id"]]).fetchone()[0]
        game_["player_black_name"] = db.execute("SELECT username FROM users WHERE id=?",
                                                [game_["player_black_id"]]).fetchone()[0]

        # Determine the "result" based on who won or if it was a draw.
        if game_["winner"] == 0:
            game_["result"] = "1/2 - 1/2"
        elif game_["winner"] == game_["player_white_id"]:
            game_["result"] = "1 - 0"
        else:
            game_["result"] = "0 - 1"

    db.close()
    return render_template("history.html", games=games_, username=username)
