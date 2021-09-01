from chesscorpy.helpers import get_player_colors, determine_player_colors


def test_get_player_colors():
    assert get_player_colors(5, 5) == ('White', 'black')
    assert get_player_colors(5, 2) == ('Black', 'white')


def test_determine_player_colors():
    # TODO: Test 'random' color
    assert determine_player_colors('white', 1, 2) == (1, 2)
    assert determine_player_colors('black', 1, 2) == (2, 1)
