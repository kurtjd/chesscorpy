from werkzeug.security import check_password_hash
from . import constants, input_validation, database, helpers, user


def for_register(username, password, email, rating):
    """ Handles errors for the register route. """

    # TODO: More error checking (ie valid email, email length, etc)
    error_msgs = {
        input_validation.Username.NONE: "Please provide a username.",
        input_validation.Username.PUBLIC: "'Public' may not be used as a username.",
        input_validation.Username.TOO_LONG: f"Username cannot be greater than {constants.USERNAME_MAX_LEN} "
                                            "characters.",
        input_validation.Password.NONE: "Please provide a password.",
        input_validation.Email.NONE: "Please provide an email address.",
        input_validation.Rating.OUT_OF_BOUNDS: f"Rating must be a number between {constants.MIN_RATING} and "
                                               f"{constants.MAX_RATING}"
    }

    username_check = input_validation.Username.check_valid(username)
    password_check = input_validation.Password.check_valid(password)
    email_check = input_validation.Email.check_valid(email)
    rating_check = input_validation.Rating.check_valid(rating)

    error_msg = None
    if username_check in error_msgs:
        error_msg = error_msgs[username_check]
    elif password_check in error_msgs:
        error_msg = error_msgs[password_check]
    elif email_check in error_msgs:
        error_msg = error_msgs[email_check]
    elif rating_check in error_msgs:
        error_msg = error_msgs[rating_check]

    if error_msg is not None:
        return helpers.error(error_msg, 400)

    # Make sure username is not already taken
    if database.sql_exec(constants.DATABASE_FILE, "SELECT username FROM users WHERE username=?",
                         [username], False, False):
        return helpers.error("Username already exists", 400)


def for_login_input(username, password):
    """ Handles errors for the input of the login route. """

    error_msgs = {
        input_validation.Username.NONE: "Please provide a username.",
        input_validation.Password.NONE: "Please provide a password."
    }

    username_check = input_validation.Username.check_valid(username)
    password_check = input_validation.Password.check_valid(password)

    error_msg = None
    if username_check in error_msgs:
        error_msg = error_msgs[username_check]
    elif password_check in error_msgs:
        error_msg = error_msgs[password_check]

    if error_msg is not None:
        return helpers.error(error_msg, 400)


def for_login_sql(user_, password):
    """ Handles errors for the SQL of the login route. """

    # Make sure username exists.
    if not user_:
        return helpers.error("User does not exist.", 400)

    # Make sure username and password combination is valid.
    if not check_password_hash(user_["password"], password):
        return helpers.error("Username and password combination is invalid.", 400)


def for_newgame_input(username, color, turnlimit, minrating, maxrating):
    """ Handles errors for the newgame route. """

    error_msgs = {
        input_validation.Username.NONE: "Please enter the name of the user you wish to challenge.",
        input_validation.GameColor.NONE: "Please select the color you wish to play.",
        input_validation.GameColor.BAD_COLOR: "Please enter a valid color.",
        input_validation.TurnLimit.NONE: "Please enter a turn limit in days.",
        input_validation.TurnLimit.OUT_OF_BOUNDS: "Please enter a turn limit greater than 0.",
        input_validation.GameRatings.MIN_NONE: "Please enter the minimum rating you wish for "
                                               "people to see your challenge.",
        input_validation.GameRatings.MIN_OUT_OF_BOUNDS: "Please enter a minimum rating between "
                                                        f"{constants.MIN_RATING} and {constants.MAX_RATING}.",
        input_validation.GameRatings.MIN_TOO_HIGH: "Please enter a minimum rating that is "
                                                   "less than or equal to the maximum rating.",
        input_validation.GameRatings.MAX_NONE: "Please enter the maximum rating you wish for "
                                               "people to see your challenge.",
        input_validation.GameRatings.MAX_OUT_OF_BOUNDS: "Please enter a maximum rating between "
                                                        f"{constants.MIN_RATING} and {constants.MAX_RATING}.",
    }

    username_check = input_validation.Username.check_valid(username)
    color_check = input_validation.GameColor.check_valid(color)
    turnlimit_check = input_validation.TurnLimit.check_valid(turnlimit)
    ratings_check = input_validation.GameRatings.check_valid(minrating, maxrating)

    error_msg = None
    if username_check in error_msgs:
        error_msg = error_msgs[username_check]
    elif color_check in error_msgs:
        error_msg = error_msgs[color_check]
    elif turnlimit_check in error_msgs:
        error_msg = error_msgs[turnlimit_check]
    elif ratings_check in error_msgs:
        error_msg = error_msgs[ratings_check]

    if error_msg is not None:
        return helpers.error(error_msg, 400)


def for_newgame_opponent(opponent):
    if not opponent:
        return helpers.error("Please enter a valid user to challenge.", 400)
    elif opponent["id"] == user.get_logged_in_id():
        return helpers.error("You cannot challenge yourself.", 400)
