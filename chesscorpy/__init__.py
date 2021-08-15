import random
import datetime
import flask_session
from flask import Flask, render_template, session, redirect, request
from werkzeug.security import generate_password_hash
from . import constants, helpers, database, input_validation, handle_errors

# Initialize Flask
app = Flask(__name__)

# Configure sessions
app.config["SESSION_TYPE"] = "filesystem"
flask_session.Session(app)


# Define routes
@app.route("/")
def index():
    """ Displays the homepage if user is not logged in, otherwise redirects them to the lobby. """

    # If user is already logged in, render different page.
    if session.get(constants.USER_SESSION) is not None:
        user_data = helpers.get_user_data(session[constants.USER_SESSION])

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
        notifications = 0 if not request.form.get("notifications") else 1

        # If rating is not a number, silently set it to default.
        try:
            rating = round(int(request.form.get("rating")))
        except ValueError:
            rating = constants.DEFAULT_RATING

        errors = handle_errors.for_register(username, password, email, rating)
        if errors:
            return errors

        # Finally create new user in database
        database.sql_exec(constants.DATABASE_FILE, "INSERT INTO users (username,password,email,rating,notifications) "
                                                   "VALUES(?,?,?,?,?)", [username, generate_password_hash(password),
                                                                         email, rating, notifications], False, False)

        # Auto login user
        user_id = database.sql_exec(constants.DATABASE_FILE, "SELECT id FROM users WHERE username=?", [username], False)
        session[constants.USER_SESSION] = user_id["id"]

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

        errors = handle_errors.for_login_input(username, password)
        if errors:
            return errors

        # Retrieve user data by username.
        user = database.sql_exec(constants.DATABASE_FILE,
                                 "SELECT id,username,password FROM users WHERE LOWER(username)=?", [username], False)

        errors = handle_errors.for_login_sql(user, password)
        if errors:
            return errors

        # If valid, create session with user's id
        session[constants.USER_SESSION] = user["id"]

        return redirect("/")
    else:
        return render_template("login.html")


@app.route("/logout")
@helpers.login_required
def logout():
    """ Logs a user out. """

    # Delete user's session and return to homepage.
    session.clear()
    return redirect("/")


@app.route("/opengames")
@helpers.login_required
def opengames():
    """ Displays a list of public or private game requests and allows users to sort and accept these requests. """

    # Selects all games that the current user has not created themselves, which are challenging the public,
    # which have rating requirements meeting the current user's rating, OR are direct requests.
    if not request.args.get("direct"):
        rows = database.sql_exec(constants.DATABASE_FILE,
                                 "SELECT game_requests.id,game_requests.turn_day_limit,game_requests.color,"
                                 "game_requests.timestamp,users.username,users.rating FROM game_requests JOIN users ON "
                                 "game_requests.user_id=users.id WHERE opponent_id=? AND user_id!=? AND "
                                 "(SELECT rating FROM users WHERE id=? LIMIT 1) BETWEEN min_rating AND max_rating",
                                 [constants.PUBLIC_USER_ID, session[constants.USER_SESSION],
                                  session[constants.USER_SESSION]], True, False)
    else:
        rows = database.sql_exec(constants.DATABASE_FILE,
                                 "SELECT game_requests.id,game_requests.turn_day_limit,game_requests.color,"
                                 "game_requests.timestamp,users.username,users.rating FROM game_requests JOIN users ON"
                                 " game_requests.user_id=users.id WHERE opponent_id=?",
                                 [session[constants.USER_SESSION]], True, False)

    return render_template("opengames.html", games=rows)


@app.route("/newgame", methods=["GET", "POST"])
@helpers.login_required
def newgame():
    """ Allows users to create a game request. """

    if request.method == "POST":
        username = request.form.get("username").lower()
        color = request.form.get("color")
        turnlimit = None if not request.form.get("turnlimit").isdigit() else int(request.form.get("turnlimit"))
        minrating = None if not request.form.get("minrating").isdigit() else int(request.form.get("minrating"))
        maxrating = None if not request.form.get("maxrating").isdigit() else int(request.form.get("maxrating"))
        public = 0 if not request.form.get("public") else 1

        errors = handle_errors.for_newgame(username, color, turnlimit, minrating, maxrating)
        if errors:
            return errors

        # Check that the user someone wants to challenge actually exists if this is not a challenge to the public.
        if username != "public":
            opponent_id = database.sql_exec(constants.DATABASE_FILE, "SELECT id FROM users WHERE LOWER(username)=?",
                                            [username], False)

            if not opponent_id:
                return helpers.error("Please enter a valid user to challenge.", 400)

            opponent_id = opponent_id["id"]

            # Don't let dingdongs challenge themselves.
            if opponent_id == session[constants.USER_SESSION]:
                return helpers.error("You cannot challenge yourself.", 400)
        else:
            opponent_id = constants.PUBLIC_USER_ID

        # Now enter the challenge into the database.
        database.sql_exec(constants.DATABASE_FILE,
                          "INSERT INTO game_requests (user_id,opponent_id,turn_day_limit,"
                          "min_rating,max_rating,color,public) VALUES(?,?,?,?,?,?,?)",
                          [session[constants.USER_SESSION], opponent_id, turnlimit,
                           minrating, maxrating, color, public])

        return redirect("/opengames")
    else:
        return render_template("newgame.html")


@app.route("/start")
@helpers.login_required
def start():
    """ Creates a game from a game request. """

    request_id = request.args.get("id")

    # Don't allow blank or invalid request IDs.
    if not request_id or not request_id.isdigit():
        return redirect("/")

    # Make sure game request exists and that user is authorized to accept the request.
    game_request = database.sql_exec(constants.DATABASE_FILE,
                                     "SELECT * FROM game_requests WHERE id=? AND (opponent_id=0 OR opponent_id=?)",
                                     [request_id, session[constants.USER_SESSION]], False)

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
    game_id = database.sql_exec(constants.DATABASE_FILE,
                                "INSERT INTO games (player_white_id,player_black_id,turn_day_limit,to_move,public) "
                                "VALUES(?,?,?,?,?)",
                                [white_id, black_id, game_request["turn_day_limit"],
                                 white_id, game_request["public"]], False, False, True)

    # Delete game request from database.
    database.sql_exec(constants.DATABASE_FILE, "DELETE FROM game_requests WHERE id=?", [request_id])

    # Jump to the newly created game.
    return redirect(f"/game?id={game_id}")


@app.route("/game")
@helpers.login_required
def game():
    """ Generates a game board based on the status of the game and allows user to make moves. """

    game_id = request.args.get("id")

    # Select game if it exists and the user is either a player in the game or the game is public.
    game_data = database.sql_exec(constants.DATABASE_FILE,
                                  "SELECT * FROM games WHERE id=? AND (player_white_id=? OR "
                                  "player_black_id=? OR public=1)",
                                  [game_id, session[constants.USER_SESSION], session[constants.USER_SESSION]], False)

    # Error handling
    if not game_data:
        return redirect("/")

    return render_template("game.html", game_data=game_data)


@app.route("/mygames")
@helpers.login_required
def mygames():
    """ Displays the active games of the user. """

    my_move = request.args.get("my_move")

    # Either display all active games or only games where it's the user's turn to move.
    if my_move:
        games_ = database.sql_exec(constants.DATABASE_FILE,
                                   "SELECT * FROM games WHERE to_move=? AND "
                                   "(status='no_move' OR status='in_progress')", [session[constants.USER_SESSION]],
                                   True, False)
    else:
        games_ = database.sql_exec(constants.DATABASE_FILE,
                                   "SELECT * FROM games WHERE player_white_id=? OR player_black_id=? AND "
                                   "(status='no_move' OR status='in_progress')",
                                   [session[constants.USER_SESSION], session[constants.USER_SESSION]], True, False)

    # Add extra keys into games list for opponent info and user's color.
    # Might be able to simplify this with a fancier SQL statement, but it works fine for now.
    games_ = [dict(game_) for game_ in games_]
    for game_ in games_:
        # Determine's user's and opponent's colors in game.
        game_["my_color"], opponent_color = helpers.player_colors(game_["player_white_id"],
                                                                  session[constants.USER_SESSION])

        opponent = database.sql_exec(constants.DATABASE_FILE, "SELECT id,username FROM users WHERE id=?",
                                     [game_[f"player_{opponent_color}_id"]], False)

        game_["opponent_name"] = opponent["username"]
        game_["opponent_id"] = opponent["id"]

        game_["player_to_move"] = database.sql_exec(constants.DATABASE_FILE, "SELECT username FROM users WHERE id=?",
                                                    [game_["to_move"]], False, False)[0]

        # Determines how much time left for the player who's turn it is to move.
        # Works by getting the time the move started, adds the turn limit to that time,
        # and then subtracts the current time from the total.
        game_["time_to_move"] = (datetime.datetime.strptime(game_["move_start_time"], "%Y-%m-%d %H:%M:%S") +
                                 (datetime.timedelta(days=game_["turn_day_limit"])) -
                                 datetime.datetime.now().replace(microsecond=0))

    # db.close()
    return render_template("mygames.html", games=games_)


@app.route("/history")
@helpers.login_required
def history():
    """ Displays the game history of a user. """

    user_id = request.args.get("id")

    # Check that the user exists and get its username.
    user = database.sql_exec(constants.DATABASE_FILE, "SELECT username FROM users WHERE id=?", [user_id], False, False)

    if not user:
        return helpers.error("That user does not exist.", 400)

    username = user[0]

    # Select completed games from the given user which are either
    # publically viewable or were played by the logged-in user.
    games_ = database.sql_exec(constants.DATABASE_FILE,
                               "SELECT * FROM games WHERE (public=1 OR player_white_id=? OR player_black_id=?) AND "
                               "(player_white_id=? OR player_black_id=?) AND status!='no_move' AND "
                               "status!='in_progress'", [session[constants.USER_SESSION],
                                                         session[constants.USER_SESSION], user_id, user_id],
                               True, False)

    # Go through each game and change/add some data to make it more human readable.
    games_ = [dict(game_) for game_ in games_]
    for game_ in games_:
        # Get the names of the players.
        game_["player_white_name"] = database.sql_exec(constants.DATABASE_FILE, "SELECT username FROM users WHERE id=?",
                                                       [game_["player_white_id"]], False, False)[0]
        game_["player_black_name"] = database.sql_exec(constants.DATABASE_FILE, "SELECT username FROM users WHERE id=?",
                                                       [game_["player_black_id"]], False, False)[0]

        # Determine the "result" based on who won or if it was a draw.
        if game_["winner"] == 0:
            game_["result"] = "1/2 - 1/2"
        elif game_["winner"] == game_["player_white_id"]:
            game_["result"] = "1 - 0"
        else:
            game_["result"] = "0 - 1"

    return render_template("history.html", games=games_, username=username)
