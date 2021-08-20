from chesscorpy import user
from chesscorpy.user import set_rating


def test_set_rating():
    assert set_rating(1200) == 1200
    assert set_rating("1200") == 1200
    assert set_rating("") == user.DEFAULT_RATING
    assert set_rating("Not valid rating") == user.DEFAULT_RATING
