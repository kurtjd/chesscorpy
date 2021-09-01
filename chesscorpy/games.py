import datetime

from . import database, user, helpers, handle_errors


class Status:
    NO_MOVE = 'no_move'
    IN_PROGRESS = 'in_progress'
    CHECKMATE = 'checkmate'
    TIMEOUT = 'timeout'
    STALEMATE = 'stalemate'
    DRAW = 'draw'


def get_public_requests():
    """Retrieves a list of public game requests."""

    query = ('SELECT game_requests.id, game_requests.turn_day_limit, '
             'game_requests.color, game_requests.timestamp, users.username, '
             'users.rating FROM game_requests JOIN users ON '
             'game_requests.user_id = users.id WHERE opponent_id = ? AND '
             'user_id != ? AND (SELECT rating FROM users WHERE id = ? LIMIT 1)'
             ' BETWEEN min_rating AND max_rating')
    query_args = [user.PUBLIC_USER_ID] + [user.get_logged_in_id()] * 2

    return database.sql_exec(database.DATABASE_FILE, query, query_args)


def get_direct_requests():
    """Retrieves a list of direct game requests to the logged in user."""

    query = ('SELECT game_requests.id, game_requests.turn_day_limit, '
             'game_requests.color, game_requests.timestamp, users.username, '
             'users.rating FROM game_requests JOIN users ON '
             'game_requests.user_id = users.id WHERE opponent_id = ?')
    query_args = [user.get_logged_in_id()]

    return database.sql_exec(database.DATABASE_FILE, query, query_args)


def create_request(user_id, opponent_id, turnlimit, minrating, maxrating,
                   color, is_public):
    """Creates a new game request."""

    query = ('INSERT INTO game_requests (user_id, opponent_id, '
             'turn_day_limit, min_rating, max_rating, color, public) '
             'VALUES(?, ?, ?, ?, ?, ?, ?)')
    query_args = [user_id, opponent_id, turnlimit, minrating, maxrating,
                  color, is_public]

    database.sql_exec(database.DATABASE_FILE, query, query_args)


def delete_request(request_id):
    """Deletes a game request."""

    database.sql_exec(database.DATABASE_FILE,
                      'DELETE FROM game_requests WHERE id = ?', [request_id])


def get_request_data_if_authed(request_id, user_id, fields=('*',)):
    """ Retrieves game request data if the user is authorized to see it. """

    query = (f'SELECT {",".join(fields)} FROM game_requests WHERE id = ? AND '
             f'(opponent_id = {user.PUBLIC_USER_ID} OR opponent_id = ?)')
    query_args = [request_id, user_id]

    return database.sql_exec(database.DATABASE_FILE, query, query_args, False)


def create_game(white_id, black_id, turnlimit, is_public):
    """Creates a new game and returns its id."""

    query = ('INSERT INTO games (player_white_id, player_black_id, '
             'turn_day_limit ,to_move, public) VALUES(?, ?, ?, ?, ?)')
    query_args = [white_id, black_id, turnlimit, white_id, is_public]

    return database.sql_exec(database.DATABASE_FILE, query, query_args,
                             False, True)


def get_game_data_if_authed(game_id, user_id, auth_public=True):
    """Retrieves game data if the user is authorized to see it."""

    public = ' OR public = 1' if auth_public else ''

    query = ('SELECT * FROM games WHERE id = ? AND (player_white_id = ? OR '
             f'player_black_id = ?{public}) LIMIT 1')
    query_args = [game_id] + [user_id] * 2

    return database.sql_exec(database.DATABASE_FILE, query, query_args, False)


def get_game_data_if_to_move(game_id, user_id):
    """Retrieves game data if the user is next to move."""

    query = f'SELECT * FROM games WHERE id = ? AND to_move = ? LIMIT 1'
    query_args = [game_id, user_id]

    return database.sql_exec(database.DATABASE_FILE, query, query_args, False)


def get_active_games(user_id):
    """Retrieves a list of active games for a user."""

    query = ('SELECT * FROM games WHERE (player_white_id = ? OR '
             f'player_black_id = ?) AND (status = "{Status.NO_MOVE}" OR '
             f'status = "{Status.IN_PROGRESS}") AND '
             '(public = 1 OR player_white_id = ? OR player_black_id = ?)')
    query_args = ([user_id] * 2) + ([user.get_logged_in_id()] * 2)

    return database.sql_exec(database.DATABASE_FILE, query, query_args)


def get_active_games_to_move(user_id):
    """Retrieves a list of active games for a user
    where it's also the user's turn to move.
    """

    query = (f'SELECT * FROM games WHERE to_move = ? AND '
             f'(status = "{Status.NO_MOVE}" OR '
             f'status = "{Status.IN_PROGRESS}")')
    query_args = [user_id]

    return database.sql_exec(database.DATABASE_FILE, query, query_args)


def get_game_history_if_authed(player_id, viewer_id):
    """Retrieves a list of completed games of a user
    if the viewer is authorized to see it.
    """

    query = ('SELECT * FROM games WHERE (public = 1 OR player_white_id = ? OR '
             'player_black_id = ?) AND (player_white_id = ? OR '
             f'player_black_id = ?) AND status != "{Status.NO_MOVE}" AND '
             f'status != "{Status.IN_PROGRESS}"')
    query_args = [viewer_id] * 2 + [player_id] * 2

    return database.sql_exec(database.DATABASE_FILE, query, query_args)


def format_active_games(games_data):
    """Adds/modifies some things for better readability."""

    # Add extra keys into games list for opponent info and user's color.
    games_data = database.rows_to_list(games_data)
    for game_ in games_data:
        white = user.get_data_by_id(game_['player_white_id'],
                                    ['id', 'username'])
        game_['white_name'] = white['username']
        game_['white_id'] = white['id']

        black = user.get_data_by_id(game_['player_black_id'],
                                    ['id', 'username'])
        game_['black_name'] = black['username']
        game_['black_id'] = black['id']

        game_['player_to_move'] = user.get_data_by_id(game_['to_move'],
                                                      ['username'])['username']
        game_['time_to_move'] = (
            helpers.get_turn_time_left(game_['move_start_time'],
                                       game_['turn_day_limit']))

    return games_data


def format_game_history(games_data):
    """Adds/modifies some things for better readability."""

    games_data = database.rows_to_list(games_data)
    for game_ in games_data:
        game_['player_white_name'] = (
            user.get_data_by_id(game_['player_white_id'],
                                ['username'])['username'])
        game_['player_black_name'] = (
            user.get_data_by_id(game_['player_black_id'],
                                ['username'])['username'])

        # Determine the 'result' based on who won or if it was a draw.
        if game_['winner'] == 0:
            game_['result'] = '1/2 - 1/2'
        elif game_['winner'] == game_['player_white_id']:
            game_['result'] = '1 - 0'
        else:
            game_['result'] = '0 - 1'

    return games_data


def get_opponent_id(username):
    """Returns an opponent id based on given username."""

    if username != 'public':
        opponent = user.get_data_by_name(username, ['id'])

        errors = handle_errors.for_newgame_opponent(opponent)
        if errors:
            return errors

        return opponent['id']
    else:
        return user.PUBLIC_USER_ID


def get_games():
    """Retrieves all active games."""

    query = (f'SELECT * FROM games WHERE status == "{Status.NO_MOVE}" '
             f'OR status == "{Status.IN_PROGRESS}"')

    return database.sql_exec(database.DATABASE_FILE, query)


def handle_timeouts(mail):
    """Checks to see if a player has ran out of time in each game."""

    all_games = get_games()

    for game in all_games:
        # Check if any player has timed out.
        if helpers.get_turn_time_left(
                game['move_start_time'],
                game['turn_day_limit']) < datetime.timedelta():
            if game['to_move'] == game['player_white_id']:
                winner = game['player_black_id']
            else:
                winner = game['player_white_id']

            # If so, update game status.
            query = (f'UPDATE games SET status = "{Status.TIMEOUT}", '
                     f'winner = {winner} WHERE id = {game["id"]}')
            database.sql_exec(database.DATABASE_FILE, query)

            # Then email the loser.
            loser_data = user.get_data_by_id(game['to_move'],
                                             ['id', 'username', 'email'])
            msg = (
                f'Hi {loser_data["username"]},\n\n'
                'Unfortunately you have lost a game due to timeout.\n\n'
                'From,\n'
                'ChessCorPyBot'
            )
            helpers.send_mail(mail, loser_data['email'], 'Game Update', msg,
                              loser_data['id'])
