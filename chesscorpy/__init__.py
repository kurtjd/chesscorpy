import random
import datetime
import flask_session
from flask import Flask, render_template, redirect, request
from . import constants, helpers, database, input_validation, handle_errors, user, games

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
    if user.logged_in():
        return render_template("/index_loggedin.html", user_data=user.get_data_by_id(user.get_logged_in_id()))
    else:
        return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """ Allows a new user to register. """

    # If user is logged in, just go back to home page.
    if user.logged_in():
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
        user.create(username, password, email, rating, notifications)

        # Auto login user
        user.auto_login(username)

        return redirect("/")
    else:
        return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """ Allows a user to login. """

    # If user is logged in, just go back to home page.
    if user.logged_in():
        return redirect("/")

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        errors = handle_errors.for_login_input(username, password)
        if errors:
            return errors

        # Retrieve user data by username.
        user_ = user.get_data_by_name(username, ["id", "username", "password"])

        errors = handle_errors.for_login_sql(user_, password)
        if errors:
            return errors

        # If valid, create session with user's id
        user.create_session(user_["id"])

        return redirect("/")
    else:
        return render_template("login.html")


@app.route("/logout")
@helpers.login_required
def logout():
    """ Logs a user out. """

    # Delete user's session and return to homepage.
    user.delete_session()
    return redirect("/")


@app.route("/opengames")
@helpers.login_required
def opengames():
    """ Displays a list of public or private game requests and allows users to sort and accept these requests. """

    games_ = games.get_direct_requests() if request.args.get("direct") else games.get_public_requests()

    return render_template("opengames.html", games=games_)


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
        is_public = 0 if not request.form.get("public") else 1

        errors = handle_errors.for_newgame_input(username, color, turnlimit, minrating, maxrating)
        if errors:
            return errors

        # Check that the user someone wants to challenge actually exists if this is not a challenge to the public.
        if username != "public":
            opponent = user.get_data_by_name(username, ["id"])

            errors = handle_errors.for_newgame_opponent(opponent)
            if errors:
                return errors

            opponent_id = opponent["id"]
        else:
            opponent_id = constants.PUBLIC_USER_ID

        # Now enter the challenge into the database.
        games.create_request(user.get_logged_in_id(), opponent_id, turnlimit, minrating, maxrating, color, is_public)

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
    game_request = games.get_request_data_if_authed(request_id, user.get_logged_in_id())

    if not game_request:
        return redirect("/")

    # Determine which player is which color.
    if game_request["color"] == "white":
        white_id = game_request["user_id"]
        black_id = user.get_logged_in_id()
    elif game_request["color"] == "black":
        white_id = user.get_logged_in_id()
        black_id = game_request["user_id"]
    else:
        # Assign colors randomly.
        random.seed(datetime.datetime.now().timestamp())

        if random.randint(0, 1) == 1:
            white_id = game_request["user_id"]
            black_id = user.get_logged_in_id()
        else:
            white_id = user.get_logged_in_id()
            black_id = game_request["user_id"]

    # Create game based off data in the game request.
    game_id = games.create_game(white_id, black_id, game_request["turn_day_limit"], game_request["public"])

    # Delete game request from database.
    games.delete_request(request_id)

    # Jump to the newly created game.
    return redirect(f"/game?id={game_id}")


@app.route("/game")
@helpers.login_required
def game():
    """ Generates a game board based on the status of the game and allows user to make moves. """

    game_id = request.args.get("id")

    # Select game if it exists and the user is either a player in the game or the game is public.
    game_data = games.get_game_data_if_authed(game_id, user.get_logged_in_id())

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
        games_ = games.get_active_games_to_move(user.get_logged_in_id())
    else:
        games_ = games.get_active_games(user.get_logged_in_id())

    # Add extra keys into games list for opponent info and user's color.
    # Might be able to simplify this with a fancier SQL statement, but it works fine for now.
    games_ = [dict(game_) for game_ in games_]
    for game_ in games_:
        # Determine's user's and opponent's colors in game.
        game_["my_color"], opponent_color = helpers.player_colors(game_["player_white_id"], user.get_logged_in_id())

        opponent = user.get_data_by_id(game_[f"player_{opponent_color}_id"], ["id", "username"])

        game_["opponent_name"] = opponent["username"]
        game_["opponent_id"] = opponent["id"]
        game_["player_to_move"] = user.get_data_by_id(game_["to_move"], ["username"])[0]
        game_["time_to_move"] = helpers.get_turn_time_left(game_["move_start_time"], game_["turn_day_limit"])

    return render_template("mygames.html", games=games_)


@app.route("/history")
@helpers.login_required
def history():
    """ Displays the game history of a user. """

    user_id = request.args.get("id")

    # Check that the user exists and get its username.
    user_ = user.get_data_by_id(user_id, ["username"])
    if not user_:
        return helpers.error("That user does not exist.", 400)

    username = user_[0]

    # Select completed games from the given user which are either
    # publically viewable or were played by the logged-in user.
    games_ = games.get_game_history_if_authed(user_id, user.get_logged_in_id())

    # Go through each game and change/add some data to make it more human readable.
    games_ = [dict(game_) for game_ in games_]
    for game_ in games_:
        game_["player_white_name"] = user.get_data_by_id(game_["player_white_id"], ["username"])[0]
        game_["player_black_name"] = user.get_data_by_id(game_["player_black_id"], ["username"])[0]

        # Determine the "result" based on who won or if it was a draw.
        if game_["winner"] == 0:
            game_["result"] = "1/2 - 1/2"
        elif game_["winner"] == game_["player_white_id"]:
            game_["result"] = "1 - 0"
        else:
            game_["result"] = "0 - 1"

    return render_template("history.html", games=games_, username=username)
