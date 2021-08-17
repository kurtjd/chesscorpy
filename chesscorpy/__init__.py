import flask_session
from flask import Flask, render_template, redirect, request, jsonify
from . import constants, helpers, database, input_validation, handle_errors, user, games, handle_move, game_statuses


app = Flask(__name__)
app.config["SESSION_TYPE"] = "filesystem"
flask_session.Session(app)


@app.route("/")
def index():
    """ Displays the homepage if user is not logged in, otherwise display user page. """

    if user.logged_in():
        return render_template("/index_loggedin.html", user_data=user.get_data_by_id(user.get_logged_in_id()))
    else:
        return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """ Allows a new user to register. """

    if user.logged_in():
        return redirect("/")

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        email = request.form.get("email")
        notifications = 0 if not request.form.get("notifications") else 1
        rating = user.set_rating_from_str(request.form.get("rating"))

        errors = handle_errors.for_register(username, password, email, rating)
        if errors:
            return errors

        user.create(username, password, email, rating, notifications)
        user.auto_login(username)

        return redirect("/")
    else:
        return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """ Allows a user to login. """

    if user.logged_in():
        return redirect("/")

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        errors = handle_errors.for_login_input(username, password)
        if errors:
            return errors

        user_ = user.get_data_by_name(username, ["id", "username", "password"])

        errors = handle_errors.for_login_sql(user_, password)
        if errors:
            return errors

        user.create_session(user_["id"])

        return redirect("/")
    else:
        return render_template("login.html")


@app.route("/logout")
@helpers.login_required
def logout():
    """ Logs a user out. """

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

        games.create_request(user.get_logged_in_id(), games.get_opponent_id(username), turnlimit, minrating,
                             maxrating, color, is_public)

        return redirect("/opengames")
    else:
        return render_template("newgame.html")


@app.route("/start")
@helpers.login_required
def start():
    """ Creates a game from a game request. """

    request_id = request.args.get("id")

    if not request_id or not request_id.isdigit():
        return redirect("/")

    game_request = games.get_request_data_if_authed(request_id, user.get_logged_in_id())

    if not game_request:
        return redirect("/")

    white_id, black_id = helpers.determine_player_colors(game_request["color"], game_request["user_id"],
                                                         user.get_logged_in_id())

    game_id = games.create_game(white_id, black_id, game_request["turn_day_limit"], game_request["public"])
    games.delete_request(request_id)

    return redirect(f"/game?id={game_id}")


@app.route("/game")
@helpers.login_required
def game():
    """ Generates a game board based on the status of the game and allows user to make moves. """

    game_id = request.args.get("id")
    game_data = games.get_game_data_if_authed(game_id, user.get_logged_in_id())

    if not game_data:
        return redirect("/")

    game_data = database.row_to_dict(game_data)
    game_data["player_white_name"] = user.get_data_by_id(game_data["player_white_id"], ["username"])["username"]
    game_data["player_black_name"] = user.get_data_by_id(game_data["player_black_id"], ["username"])["username"]

    if game_data["player_white_id"] == user.get_logged_in_id():
        game_data["my_color"] = "white"
    elif game_data["player_black_id"] == user.get_logged_in_id():
        game_data["my_color"] = "black"
    else:
        game_data["my_color"] = "none"

    return render_template("game.html", game_data=game_data)


@app.route("/mygames")
@helpers.login_required
def mygames():
    """ Displays the active games of the user. """

    my_move = request.args.get("my_move")

    if my_move:
        games_ = games.get_active_games_to_move(user.get_logged_in_id())
    else:
        games_ = games.get_active_games(user.get_logged_in_id())

    return render_template("mygames.html", games=games.format_active_games(games_))


@app.route("/history")
@helpers.login_required
def history():
    """ Displays the game history of a user. """

    user_id = request.args.get("id")
    user_ = user.get_data_by_id(user_id, ["username"])

    if not user_:
        return helpers.error("That user does not exist.", 400)

    username = user_["username"]
    games_ = games.get_game_history_if_authed(user_id, user.get_logged_in_id())

    return render_template("history.html", games=games.format_game_history(games_), username=username)


@app.route("/move", methods=["GET", "POST"])
@helpers.login_required
def move_request():
    """ Processes a move request for a game by a user. """

    if request.method == "POST":
        game_id = request.form.get("id")
        move = request.form.get("move")

        if not game_id or not move:
            return redirect('/')

        game_data = games.get_game_data_if_to_move(game_id, user.get_logged_in_id())

        # Don't let player move in an already completed game.
        if not game_data or (game_data["status"] != game_statuses.NO_MOVE and
                             game_data["status"] != game_statuses.IN_PROGRESS):
            return jsonify(successful=False)

        return jsonify(successful=handle_move.process_move(move, database.row_to_dict(game_data)))
    else:
        return redirect('/')
