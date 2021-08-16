from . import constants, database, user


def get_public_requests():
    """ Retrieves a list of public game requests. """

    query = "SELECT game_requests.id, game_requests.turn_day_limit, game_requests.color, game_requests.timestamp, " \
            "users.username, users.rating FROM game_requests JOIN users ON game_requests.user_id = users.id WHERE " \
            "opponent_id = ? AND user_id != ? AND (SELECT rating FROM users WHERE id = ? LIMIT 1) " \
            "BETWEEN min_rating AND max_rating"
    query_args = [constants.PUBLIC_USER_ID] + [user.get_logged_in_id()] * 2

    return database.sql_exec(constants.DATABASE_FILE, query, query_args, True, False)


def get_direct_requests():
    """ Retrieves a list of direct game requests to the logged in user. """

    query = "SELECT game_requests.id, game_requests.turn_day_limit, game_requests.color, game_requests.timestamp, " \
            "users.username, users.rating FROM game_requests JOIN users ON game_requests.user_id = users.id WHERE " \
            "opponent_id = ?"
    query_args = [user.get_logged_in_id()]

    return database.sql_exec(constants.DATABASE_FILE, query, query_args, True, False)


def create_request(user_id, opponent_id, turnlimit, minrating, maxrating, color, is_public):
    """ Creates a new game request. """

    query = "INSERT INTO game_requests (user_id, opponent_id, turn_day_limit, min_rating, max_rating, color, public) " \
            "VALUES(?, ?, ?, ?, ?, ?, ?)"
    query_args = [user_id, opponent_id, turnlimit, minrating, maxrating, color, is_public]

    database.sql_exec(constants.DATABASE_FILE, query, query_args)
