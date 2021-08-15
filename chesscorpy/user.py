from flask import session
from werkzeug.security import generate_password_hash
from . import constants, database


def get_data(userid, fields='*'):
    """ Retrieves the data of a user with the given id. """

    query = f"SELECT {','.join(fields)} FROM users WHERE id = ? LIMIT 1"
    query_args = [userid]

    return database.sql_exec(constants.DATABASE_FILE, query, query_args, False)


def logged_in():
    """ Checks if the user is logged in. """

    return True if session.get(constants.USER_SESSION) else False


def create(username, password, email, rating, notifications):
    """ Creates a new user in the database. """

    query = "INSERT INTO users (username, password, email, rating, notifications) VALUES(?, ?, ?, ?, ?)"
    query_args = [username, generate_password_hash(password), email, rating, notifications]

    database.sql_exec(constants.DATABASE_FILE, query, query_args, False, False)


def auto_login(username):
    """ Automatically logs in a user given a username. """

    query = "SELECT id FROM users WHERE username=?"
    query_args = [username]

    user_id = database.sql_exec(constants.DATABASE_FILE, query, query_args, False)
    session[constants.USER_SESSION] = user_id["id"]


def get_logged_in_id():
    """ Gets the id of the currently logged-in user. """

    return session[constants.USER_SESSION]


def create_session(userid):
    """ Creates a session for the given user id. """

    session[constants.USER_SESSION] = userid
