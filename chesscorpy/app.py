import flask_session
import flask_mail
from flask import Flask, render_template, redirect, request, jsonify, escape
from apscheduler.schedulers.background import BackgroundScheduler

from . import helpers, database, handle_errors, user, games
from . import handle_move, chat


app = Flask(__name__)

# Change depending on your mail configuration.
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'chesscorpy@gmail.com'
app.config['MAIL_PASSWORD'] = '***'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

app.config['SESSION_TYPE'] = 'filesystem'
mail = flask_mail.Mail(app)
flask_session.Session(app)


def handle_timeouts_wrap():
    """Allow for the call of mail in check_games under app context."""

    with app.app_context():
        games.handle_timeouts(mail)


# Set up the job that checks for timed out games.
game_check_job = BackgroundScheduler()
game_check_job.add_job(handle_timeouts_wrap, 'interval', seconds=30)
game_check_job.start()


@app.route('/')
def index():
    """Displays the homepage if user is not logged in,
    otherwise display user page.
    """

    if user.logged_in():
        return render_template(
            '/index_loggedin.html',
            user_data=user.get_data_by_id(user.get_logged_in_id()))
    else:
        return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Allows a new user to register."""

    if user.logged_in():
        return redirect('/')

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        notifications = 0 if not request.form.get('notifications') else 1
        rating = user.set_rating(request.form.get('rating', type=int))

        errors = handle_errors.for_register(username, password, email, rating)
        if errors:
            return errors

        user.create(username, password, email, rating, notifications)
        user.auto_login(username)

        return redirect('/')
    else:
        return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Allows a user to login."""

    if user.logged_in():
        return redirect('/')

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        errors = handle_errors.for_login_input(username, password)
        if errors:
            return errors

        user_ = user.get_data_by_name(username, ['id', 'username', 'password'])

        errors = handle_errors.for_login_sql(user_, password)
        if errors:
            return errors

        user.create_session(user_['id'])

        return redirect('/')
    else:
        return render_template('login.html')


@app.route('/logout')
@helpers.login_required
def logout():
    """Logs a user out."""

    user.delete_session()
    return redirect('/')


@app.route('/profile')
@helpers.login_required
def profile():
    """Displays the profile of a user."""

    user_id = request.args.get('id', type=int)
    user_data = user.get_data_by_id(user_id)

    if not user_data:
        return helpers.error('That user does not exist.', 400)

    return render_template('profile.html', user_data=user_data)


@app.route('/opengames')
@helpers.login_required
def opengames():
    """Displays a list of public or private game requests
    and allows users to sort and accept these requests.
    """

    if request.args.get('direct'):
        games_ = games.get_direct_requests()
    else:
        games_ = games.get_public_requests()

    return render_template('opengames.html', games=games_)


@app.route('/newgame', methods=['GET', 'POST'])
@helpers.login_required
def newgame():
    """Allows users to create a game request."""

    if request.method == 'POST':
        username = request.form.get('username').lower()
        color = request.form.get('color')
        turnlimit = request.form.get('turnlimit', type=int)
        minrating = request.form.get('minrating', type=int)
        maxrating = request.form.get('maxrating', type=int)
        is_public = 0 if not request.form.get('public') else 1

        errors = handle_errors.for_newgame_input(username, color, turnlimit,
                                                 minrating, maxrating)
        if errors:
            return errors

        games.create_request(user.get_logged_in_id(),
                             games.get_opponent_id(username), turnlimit,
                             minrating, maxrating, color, is_public)

        return redirect('/opengames')
    else:
        if request.args.get('username'):
            username = request.args.get('username')
        else:
            username = 'Public'

        return render_template('newgame.html', username=username)


@app.route('/start')
@helpers.login_required
def start():
    """Creates a game from a game request."""

    request_id = request.args.get('id', type=int)

    if not request_id:
        return redirect('/')

    game_request = games.get_request_data_if_authed(request_id,
                                                    user.get_logged_in_id())

    if not game_request:
        return redirect('/')

    white_id, black_id = helpers.determine_player_colors(
        game_request['color'], game_request['user_id'],
        user.get_logged_in_id())

    game_id = games.create_game(white_id, black_id,
                                game_request['turn_day_limit'],
                                game_request['public'])

    games.delete_request(request_id)

    return redirect(f'/game?id={game_id}')


@app.route('/game')
@helpers.login_required
def game():
    """Generates a game board based on the status of the game and
    allows user to make moves.
    """

    game_id = request.args.get('id', type=int)
    game_data = games.get_game_data_if_authed(game_id, user.get_logged_in_id())

    if not game_data:
        return redirect('/')

    game_data = database.row_to_dict(game_data)
    game_data['player_white_name'] = user.get_data_by_id(
        game_data['player_white_id'], ['username'])['username']
    game_data['player_black_name'] = user.get_data_by_id(
        game_data['player_black_id'], ['username'])['username']

    if game_data['player_white_id'] == user.get_logged_in_id():
        game_data['my_color'] = 'white'
    elif game_data['player_black_id'] == user.get_logged_in_id():
        game_data['my_color'] = 'black'
    else:
        game_data['my_color'] = 'none'

    return render_template('game.html', game_data=game_data)


@app.route('/activegames')
@helpers.login_required
def activegames():
    """Displays the active games of a user."""

    my_move = request.args.get('my_move')

    if request.args.get('id'):
        user_id = request.args.get('id', type=int)
    else:
        user_id = user.get_logged_in_id()

    if my_move and user_id == user.get_logged_in_id():
        games_ = games.get_active_games_to_move(user_id)
    else:
        games_ = games.get_active_games(user_id)

    username = user.get_data_by_id(user_id, ['username'])['username']

    if user_id == user.get_logged_in_id():
        my_games = True
    else:
        my_games = False

    return render_template('activegames.html',
                           games=games.format_active_games(games_),
                           username=username, my_games=my_games)


@app.route('/history')
@helpers.login_required
def history():
    """Displays the game history of a user."""

    user_id = request.args.get('id', type=int)
    user_ = user.get_data_by_id(user_id, ['username'])

    if not user_:
        return helpers.error('That user does not exist.', 400)

    username = user_['username']
    games_ = games.get_game_history_if_authed(user_id, user.get_logged_in_id())

    return render_template('history.html',
                           games=games.format_game_history(games_),
                           username=username)


@app.route('/settings', methods=['GET', 'POST'])
@helpers.login_required
def settings():
    """Allows user to change settings."""

    if request.method == 'POST':
        notify = 0 if not request.form.get('notifications') else 1

        user.update_settings(user.get_logged_in_id(), notify)
        return redirect('/')
    else:
        notify = int(user.get_data_by_id(user.get_logged_in_id(),
                                         ['notifications'])['notifications'])
        return render_template('settings.html', notify=notify)


@app.route('/move', methods=['GET', 'POST'])
@helpers.login_required
def move_request():
    """Processes a move request for a game by a user."""

    if request.method == 'POST':
        game_id = request.form.get('id', type=int)
        move = request.form.get('move')
        game_data = games.get_game_data_if_to_move(game_id,
                                                   user.get_logged_in_id())

        # Don't let user move in an already completed game
        # or game they are not a player of.
        if not game_data or not move or (
                game_data['status'] != games.Status.NO_MOVE
                and game_data['status'] != games.Status.IN_PROGRESS
        ):
            return jsonify(successful=False)

        # Need app context for process_move to send mail.
        with app.app_context():
            move_success = handle_move.process_move(
                move, database.row_to_dict(game_data), mail)

        return jsonify(successful=move_success)
    else:
        return redirect('/')


@app.route('/chat', methods=['GET', 'POST'])
@helpers.login_required
def handle_chat():
    """Sends or retrieves chat messages."""

    if request.method == 'GET':
        return jsonify(chat.get_chats(request.args.get('id', type=int)))
    else:
        game_id = request.form.get('game_id', type=int)
        user_id = request.form.get('user_id', type=int)
        msg = escape(request.form.get('msg'))

        if (not game_id or not user_id or not msg
                or len(msg) > chat.CHAT_MSG_MAX_LEN
                or user_id != user.get_logged_in_id()
                or not games.get_game_data_if_authed(game_id, user_id, False)):
            return jsonify(successful=False)

        chat.new_chat(game_id, user_id, msg)

        return jsonify(successful=True)
