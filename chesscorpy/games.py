from . import constants, database, user


def get_public_requests():
    """ Retrieves a list of public game requests. """

    query = "SELECT game_requests.id, game_requests.turn_day_limit, game_requests.color, game_requests.timestamp, " \
            "users.username, users.rating FROM game_requests JOIN users ON game_requests.user_id = users.id WHERE " \
            "opponent_id = ? AND user_id != ? AND (SELECT rating FROM users WHERE id = ? LIMIT 1) " \
            "BETWEEN min_rating AND max_rating"
    query_args = [constants.PUBLIC_USER_ID] + [user.get_logged_in_id()] * 2

    return database.sql_exec(constants.DATABASE_FILE, query, query_args)


def get_direct_requests():
    """ Retrieves a list of direct game requests to the logged in user. """

    query = "SELECT game_requests.id, game_requests.turn_day_limit, game_requests.color, game_requests.timestamp, " \
            "users.username, users.rating FROM game_requests JOIN users ON game_requests.user_id = users.id WHERE " \
            "opponent_id = ?"
    query_args = [user.get_logged_in_id()]

    return database.sql_exec(constants.DATABASE_FILE, query, query_args)


def create_request(user_id, opponent_id, turnlimit, minrating, maxrating, color, is_public):
    """ Creates a new game request. """

    query = "INSERT INTO game_requests (user_id, opponent_id, turn_day_limit, min_rating, max_rating, color, public) " \
            "VALUES(?, ?, ?, ?, ?, ?, ?)"
    query_args = [user_id, opponent_id, turnlimit, minrating, maxrating, color, is_public]

    database.sql_exec(constants.DATABASE_FILE, query, query_args)


def delete_request(request_id):
    """ Deletes a game request. """

    database.sql_exec(constants.DATABASE_FILE, "DELETE FROM game_requests WHERE id = ?", [request_id])


def get_request_data_if_authed(request_id, user_id, fields=('*',)):
    """ Retrieves game request data if the user is authorized to see it. """

    query = f"SELECT {','.join(fields)} FROM game_requests WHERE id = ? AND (opponent_id = 0 OR opponent_id = ?)"
    query_args = [request_id, user_id]

    return database.sql_exec(constants.DATABASE_FILE, query, query_args, False)


def create_game(white_id, black_id, turnlimit, is_public):
    """ Creates a new game and returns its id. """

    query = "INSERT INTO games (player_white_id, player_black_id, turn_day_limit ,to_move, public) " \
            "VALUES(?, ?, ?, ?, ?)"
    query_args = [white_id, black_id, turnlimit, white_id, is_public]

    return database.sql_exec(constants.DATABASE_FILE, query, query_args, False, True)


def get_game_data_if_authed(game_id, user_id):
    """ Retrieves game data if the user is authorized to see it. """

    query = "SELECT * FROM games WHERE id = ? AND (player_white_id = ? OR player_black_id = ? OR public = 1)"
    query_args = [game_id] + [user_id] * 2

    return database.sql_exec(constants.DATABASE_FILE, query, query_args, False)


def get_active_games(user_id):
    """ Retrieves a list of active games for a user. """

    query = "SELECT * FROM games WHERE player_white_id = ? OR player_black_id = ? AND " \
            "(status = 'no_move' OR status = 'in_progress')"
    query_args = [user_id] * 2

    return database.sql_exec(constants.DATABASE_FILE, query, query_args)


def get_active_games_to_move(user_id):
    """ Retrieves a list of active games for a user where it's also the user's turn to move. """

    query = "SELECT * FROM games WHERE to_move = ? AND (status = 'no_move' OR status = 'in_progress')"
    query_args = [user_id]

    return database.sql_exec(constants.DATABASE_FILE, query, query_args)


def get_game_history_if_authed(player_id, viewer_id):
    """ Retrieves a list of completed games of a user if the viewer is authorized to see it. """

    query = "SELECT * FROM games WHERE (public = 1 OR player_white_id = ? OR player_black_id = ?) AND " \
            "(player_white_id = ? OR player_black_id = ?) AND status != 'no_move' AND status != 'in_progress'"
    query_args = [viewer_id] * 2 + [player_id] * 2

    return database.sql_exec(constants.DATABASE_FILE, query, query_args)
