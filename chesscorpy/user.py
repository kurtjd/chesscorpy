from flask import session
from . import constants, database


def get_data(userid, fields='*'):
    """ Retrieves the data of a user with the given id. """

    return database.sql_exec(constants.DATABASE_FILE, f"SELECT {','.join(fields)} FROM users WHERE id=? LIMIT 1",
                             [userid], False)


def logged_in():
    """ Checks if the user is logged in. """

    return True if session.get(constants.USER_SESSION) else False
