from functools import wraps
from flask import redirect, session, render_template


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
        if not session.get("user_id"):
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function
