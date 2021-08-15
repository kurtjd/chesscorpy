from functools import wraps
from flask import redirect, session, render_template
from . import constants, database


def error(msg, code):
    """ Displays an error page with error message and error code. """

    return render_template("error.html", msg=msg, code=code)


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/2.0.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get(constants.USER_SESSION):
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def get_user_data(userid, fields='*'):
    """ Retrieves the data of a user with the given id. """

    return database.sql_exec(constants.DATABASE_FILE, f"SELECT {','.join(fields)} FROM users WHERE id=? LIMIT 1",
                             [userid], False)


def player_colors(white_id, user_id):
    """ Returns a tuple of colors in the order (user, opponent). """

    return ("White", "black") if white_id == user_id else ("Black", "white")
