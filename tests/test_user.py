from chesscorpy import constants
from chesscorpy.user import set_rating_from_str


def test_set_rating_from_str():
    assert set_rating_from_str("1200") == 1200
    assert set_rating_from_str("1200.2") == 1200
    assert set_rating_from_str("Not valid rating") == constants.DEFAULT_RATING
