from enum import Enum, auto
from . import user


class Username(Enum):
    VALID = auto()
    NONE = auto()
    TOO_LONG = auto()
    PUBLIC = auto()

    @classmethod
    def check_valid(cls, username):
        if not username:
            return cls.NONE
        elif len(username) > user.USERNAME_MAX_LEN:
            return cls.TOO_LONG
        elif username.lower() == 'public':
            return cls.PUBLIC
        else:
            return cls.VALID


class Password(Enum):
    VALID = auto()
    NONE = auto()

    @classmethod
    def check_valid(cls, password):
        if not password:
            return cls.NONE
        else:
            return cls.VALID


class Email(Enum):
    VALID = auto()
    NONE = auto()

    @classmethod
    def check_valid(cls, email):
        if not email:
            return cls.NONE
        else:
            return cls.VALID


class Rating(Enum):
    VALID = auto()
    NONE = auto()
    OUT_OF_BOUNDS = auto()

    @classmethod
    def check_valid(cls, rating):
        if not rating:
            return cls.NONE
        elif not (user.MIN_RATING <= rating <= user.MAX_RATING):
            return cls.OUT_OF_BOUNDS
        else:
            return cls.VALID


class GameColor(Enum):
    VALID = auto()
    NONE = auto()
    BAD_COLOR = auto()

    @classmethod
    def check_valid(cls, color):
        if not color:
            return cls.NONE
        elif color not in ('random', 'white', 'black'):
            return cls.BAD_COLOR
        else:
            return cls.VALID


class TurnLimit(Enum):
    VALID = auto()
    NONE = auto()
    OUT_OF_BOUNDS = auto()

    @classmethod
    def check_valid(cls, limit):
        if not limit:
            return cls.NONE
        elif limit < 1:
            return cls.OUT_OF_BOUNDS
        else:
            return cls.VALID


class GameRatings(Enum):
    VALID = auto()
    MIN_NONE = auto()
    MAX_NONE = auto()
    MIN_OUT_OF_BOUNDS = auto()
    MAX_OUT_OF_BOUNDS = auto()
    MIN_TOO_HIGH = auto()

    @classmethod
    def check_valid(cls, min_, max_):
        if not min_:
            return cls.MIN_NONE
        elif not max_:
            return cls.MAX_NONE
        elif not (user.MIN_RATING <= min_ <= user.MAX_RATING):
            return cls.MIN_OUT_OF_BOUNDS
        elif not (user.MIN_RATING <= max_ <= user.MAX_RATING):
            return cls.MAX_OUT_OF_BOUNDS
        elif min_ > max_:
            return cls.MIN_TOO_HIGH
        else:
            return cls.VALID
