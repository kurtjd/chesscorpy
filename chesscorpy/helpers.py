import random
import datetime
from functools import wraps
from flask import redirect, render_template
from . import user


def error(msg, code):
    """ Displays an error page with error message and error code. """

    return render_template('error.html', msg=msg, code=code)


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/2.0.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not user.logged_in():
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function


def get_player_colors(white_id, user_id):
    """ Returns a tuple of colors in the order (user, opponent). """

    return ('White', 'black') if white_id == user_id else ('Black', 'white')


def determine_player_colors(requester_color, requester_id, challenger_id):
    """ Determines which user is which color and returns a tuple in the form (player white, player black). """

    if requester_color == 'white':
        return requester_id, challenger_id
    elif requester_color == 'black':
        return challenger_id, requester_id
    else:
        # Assign colors randomly.
        random.seed(datetime.datetime.now().timestamp())

        if random.randint(0, 1) == 1:
            return requester_id, challenger_id
        else:
            return challenger_id, requester_id


def get_turn_time_left(turn_start, turnlimit):
    """ Determines how much time left a player has to move. """

    # Works by getting the time the move started, adds the turn limit to that time,
    # and then subtracts the current time from the total.
    return (datetime.datetime.strptime(turn_start, '%Y-%m-%d %H:%M:%S') +
            (datetime.timedelta(days=turnlimit)) -
            datetime.datetime.now().replace(microsecond=0))
