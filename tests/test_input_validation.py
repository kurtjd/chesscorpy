from chesscorpy import input_validation, constants


def test_username_check_valid():
    assert input_validation.Username.check_valid('') is input_validation.Username.NONE
    assert input_validation.Username.check_valid("Very Long Username This Is") is input_validation.Username.TOO_LONG
    assert input_validation.Username.check_valid("JohnDoe") is input_validation.Username.VALID
    assert input_validation.Username.check_valid('A' * constants.USERNAME_MAX_LEN) is input_validation.Username.VALID


def test_password_check_valid():
    assert input_validation.Password.check_valid('') is input_validation.Password.NONE
    assert input_validation.Password.check_valid("MyTopSecretPassword") is input_validation.Password.VALID


def test_email_check_valid():
    assert input_validation.Email.check_valid('') is input_validation.Email.NONE
    assert input_validation.Email.check_valid("johndoe@gmail.com") is input_validation.Email.VALID


def test_rating_check_valid():
    assert input_validation.Rating.check_valid('') is input_validation.Rating.NONE
    assert input_validation.Rating.check_valid(0) is input_validation.Rating.OUT_OF_BOUNDS
    assert input_validation.Rating.check_valid(-100) is input_validation.Rating.OUT_OF_BOUNDS
    assert input_validation.Rating.check_valid(9000) is input_validation.Rating.OUT_OF_BOUNDS
    assert input_validation.Rating.check_valid(2600) is input_validation.Rating.VALID
    assert input_validation.Rating.check_valid(constants.MIN_RATING) is input_validation.Rating.VALID
    assert input_validation.Rating.check_valid(constants.MAX_RATING) is input_validation.Rating.VALID


def test_gamecolor_check_valid():
    assert input_validation.GameColor.check_valid('') is input_validation.GameColor.NONE
    assert input_validation.GameColor.check_valid("red") is input_validation.GameColor.BAD_COLOR
    assert input_validation.GameColor.check_valid("white") is input_validation.GameColor.VALID
    assert input_validation.GameColor.check_valid("black") is input_validation.GameColor.VALID
    assert input_validation.GameColor.check_valid("random") is input_validation.GameColor.VALID


def test_turnlimit_check_valid():
    assert input_validation.TurnLimit.check_valid('') is input_validation.TurnLimit.NONE
    assert input_validation.TurnLimit.check_valid(0) is input_validation.TurnLimit.OUT_OF_BOUNDS
    assert input_validation.TurnLimit.check_valid(-100) is input_validation.TurnLimit.OUT_OF_BOUNDS
    assert input_validation.TurnLimit.check_valid(10) is input_validation.TurnLimit.VALID


def test_gameratings_check_valid():
    assert input_validation.GameRatings.check_valid('', '') is input_validation.GameRatings.MIN_NONE
    assert input_validation.GameRatings.check_valid('', 1200) is input_validation.GameRatings.MIN_NONE
    assert input_validation.GameRatings.check_valid(1200, '') is input_validation.GameRatings.MAX_NONE
    assert input_validation.GameRatings.check_valid(-100, 1200) is input_validation.GameRatings.MIN_OUT_OF_BOUNDS
    assert input_validation.GameRatings.check_valid(1200, 9000) is input_validation.GameRatings.MAX_OUT_OF_BOUNDS
    assert input_validation.GameRatings.check_valid(2600, 1200) is input_validation.GameRatings.MIN_TOO_HIGH
    assert input_validation.GameRatings.check_valid(1200, 2600) is input_validation.GameRatings.VALID
    assert input_validation.GameRatings.check_valid(constants.MIN_RATING, constants.MAX_RATING) is \
           input_validation.GameRatings.VALID
