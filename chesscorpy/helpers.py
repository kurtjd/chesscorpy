from functools import wraps
from flask import redirect, session, render_template
from .constants import USER_SESSION


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
        if not session.get(USER_SESSION):
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def player_colors(white_id, user_id):
    """ Returns a tuple of colors in the order (user, opponent). """

    return ("White", "black") if white_id == user_id else ("Black", "white")
