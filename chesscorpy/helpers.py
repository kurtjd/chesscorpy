from functools import wraps
from flask import redirect, session, render_template


def error(msg, code):
    return render_template("error.html", msg=msg, code=code)


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/2.0.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function
