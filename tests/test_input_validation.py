from chesscorpy import user
from chesscorpy.input_validation import Username, Password, Email, Rating, GameColor, TurnLimit, GameRatings


def test_username_check_valid():
    assert Username.check_valid('') is Username.NONE
    assert Username.check_valid('Very Long Username This Is') is Username.TOO_LONG
    assert Username.check_valid('JohnDoe') is Username.VALID
    assert Username.check_valid('A' * user.USERNAME_MAX_LEN) is Username.VALID


def test_password_check_valid():
    assert Password.check_valid('') is Password.NONE
    assert Password.check_valid('MyTopSecretPassword') is Password.VALID


def test_email_check_valid():
    assert Email.check_valid('') is Email.NONE
    assert Email.check_valid('johndoe@gmail.com') is Email.VALID


def test_rating_check_valid():
    assert Rating.check_valid('') is Rating.NONE
    assert Rating.check_valid(0) is Rating.OUT_OF_BOUNDS
    assert Rating.check_valid(-100) is Rating.OUT_OF_BOUNDS
    assert Rating.check_valid(9000) is Rating.OUT_OF_BOUNDS
    assert Rating.check_valid(2600) is Rating.VALID
    assert Rating.check_valid(user.MIN_RATING) is Rating.VALID
    assert Rating.check_valid(user.MAX_RATING) is Rating.VALID


def test_gamecolor_check_valid():
    assert GameColor.check_valid('') is GameColor.NONE
    assert GameColor.check_valid('red') is GameColor.BAD_COLOR
    assert GameColor.check_valid('white') is GameColor.VALID
    assert GameColor.check_valid('black') is GameColor.VALID
    assert GameColor.check_valid('random') is GameColor.VALID


def test_turnlimit_check_valid():
    assert TurnLimit.check_valid('') is TurnLimit.NONE
    assert TurnLimit.check_valid(0) is TurnLimit.OUT_OF_BOUNDS
    assert TurnLimit.check_valid(-100) is TurnLimit.OUT_OF_BOUNDS
    assert TurnLimit.check_valid(10) is TurnLimit.VALID


def test_gameratings_check_valid():
    assert GameRatings.check_valid('', '') is GameRatings.MIN_NONE
    assert GameRatings.check_valid('', 1200) is GameRatings.MIN_NONE
    assert GameRatings.check_valid(1200, '') is GameRatings.MAX_NONE
    assert GameRatings.check_valid(-100, 1200) is GameRatings.MIN_OUT_OF_BOUNDS
    assert GameRatings.check_valid(1200, 9000) is GameRatings.MAX_OUT_OF_BOUNDS
    assert GameRatings.check_valid(2600, 1200) is GameRatings.MIN_TOO_HIGH
    assert GameRatings.check_valid(1200, 2600) is GameRatings.VALID
    assert GameRatings.check_valid(user.MIN_RATING, user.MAX_RATING) is \
           GameRatings.VALID
