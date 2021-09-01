from flask import session
from werkzeug.security import generate_password_hash
from . import database


USERNAME_MAX_LEN = 15
DEFAULT_RATING = 1000
MIN_RATING = 1
MAX_RATING = 3000
PUBLIC_USER_ID = 0
DRAW_USER_ID = 0
USER_SESSION = 'user_id'


def get_data_by_id(userid, fields='*'):
    """ Retrieves the data of a user with the given id. """

    query = f'SELECT {",".join(fields)} FROM users WHERE id = ? LIMIT 1'
    query_args = [userid]

    return database.sql_exec(database.DATABASE_FILE, query, query_args, False)


def get_data_by_name(username, fields=('*',), case_sensitive=False):
    """ Retrieves the data of a user with the given name. """

    if not case_sensitive:
        query = f'SELECT {",".join(fields)} FROM users WHERE LOWER(username) = ? LIMIT 1'
        query_args = [username.lower()]
    else:
        query = f'SELECT {",".join(fields)} FROM users WHERE username = ? LIMIT 1'
        query_args = [username]

    return database.sql_exec(database.DATABASE_FILE, query, query_args, False)


def logged_in():
    """ Checks if the user is logged in. """

    return True if session.get(USER_SESSION) else False


def create(username, password, email, rating, notifications):
    """ Creates a new user in the database. """

    query = 'INSERT INTO users (username, password, email, rating, notifications) VALUES(?, ?, ?, ?, ?)'
    query_args = [username, generate_password_hash(password), email, rating, notifications]

    database.sql_exec(database.DATABASE_FILE, query, query_args, False)


def auto_login(username):
    """ Automatically logs in a user given a username. """

    query = 'SELECT id FROM users WHERE username=?'
    query_args = [username]

    user_id = database.sql_exec(database.DATABASE_FILE, query, query_args, False)
    create_session(user_id['id'])


def get_logged_in_id():
    """ Gets the id of the currently logged-in user. """

    return session[USER_SESSION]


def create_session(userid):
    """ Creates a session for the given user id. """

    session[USER_SESSION] = userid


def delete_session():
    """ Deletes the current user session. """

    session.clear()


def set_rating(rating):
    """ Sets the user's starting rating. """

    try:
        rating = int(rating)
    except ValueError:
        rating = DEFAULT_RATING

    return rating
