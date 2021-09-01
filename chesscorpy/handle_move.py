import datetime
import io

import chess
import chess.pgn

from . import user, database, games, helpers


def _update_game_db(game_data):
    query = ('UPDATE games SET to_move = ?, move_start_time = ?, status = ?, '
             'winner = ?, pgn = ? WHERE id = ?')
    query_args = [game_data['to_move'], game_data['move_start_time'],
                  game_data['status'], game_data['winner'], game_data['pgn'],
                  game_data['id']]

    database.sql_exec(database.DATABASE_FILE, query, query_args)


def _update_player_to_move(game_data):
    if game_data['player_white_id'] == game_data['to_move']:
        game_data['to_move'] = game_data['player_black_id']
    else:
        game_data['to_move'] = game_data['player_white_id']


def _update_game_status(game_status, game_data):
    if game_status:
        status_options = {
            game_status.termination.CHECKMATE: games.Status.CHECKMATE,
            game_status.termination.STALEMATE: games.Status.STALEMATE,
            game_status.termination.INSUFFICIENT_MATERIAL: games.Status.DRAW,
            game_status.termination.THREEFOLD_REPETITION: games.Status.DRAW
        }

        game_data['status'] = status_options[game_status.termination]

        if game_status.winner == chess.WHITE:
            win_color = 'white'
        elif game_status.winner == chess.BLACK:
            win_color = 'black'
        else:
            win_color = None

        if win_color:
            game_data['winner'] = game_data[f'player_{win_color}_id']
        else:
            game_data['winner'] = user.DRAW_USER_ID
    else:
        game_data['status'] = games.Status.IN_PROGRESS


def _update_game_data(game_data, game_pgn, game_status):
    game_data['pgn'] = game_pgn
    game_data['move_start_time'] = (
        datetime.datetime.now().replace(microsecond=0))
    _update_player_to_move(game_data)
    _update_game_status(game_status, game_data)


def _get_game_status(game):
    return game.outcome(claim_draw=True)


def _regen_pgn_headers(game, game_data):
    game.headers['Event'] = 'Correspondence Chess'
    game.headers['Site'] = 'ChessCorPy'
    game.headers['Date'] = datetime.datetime.strptime(
        game_data['timestamp'], '%Y-%m-%d %H:%M:%S').strftime('%Y.%m.%d')
    game.headers['Round'] = '-'
    game.headers['White'] = user.get_data_by_id(game_data[f'player_white_id'],
                                                ['username'])['username']
    game.headers['Black'] = user.get_data_by_id(game_data[f'player_black_id'],
                                                ['username'])['username']


def _board_load_pgn(board, pgn):
    game = chess.pgn.read_game(io.StringIO(pgn))
    for move in game.mainline_moves():
        board.push(move)


def _attempt_move(move_san, game):
    move = game.parse_san(move_san)
    if move in game.legal_moves:
        game.push(move)
        return True
    else:
        return False


def _notify_player(mail, outcome, game_data, move_san):
    if outcome:
        msg_options = {
            outcome.termination.CHECKMATE: (
                'The game has been won by checkmate.'),
            outcome.termination.STALEMATE: 'The game is a draw by stalemate.',
            outcome.termination.INSUFFICIENT_MATERIAL: (
                'The game is a draw by insufficient material.'),
            outcome.termination.THREEFOLD_REPETITION: (
                'The game is a draw by three-fold repetition.')
        }

        msg_body = msg_options[outcome.termination]
    else:
        msg_body = (f'You have {game_data["turn_day_limit"]} days '
                    'to make a move.')

    next_player = user.get_data_by_id(game_data['to_move'],
                                      ['id', 'username', 'email'])
    msg = (
        f'Hi {next_player["username"]}!\n\n'
        f'Your opponent has played the move {move_san}. '
        f'{msg_body}\n\n'
        'Your pal,\n'
        'ChessCorPyBot'
    )

    helpers.send_mail(mail, next_player['email'], 'Game Update', msg,
                      next_player['id'])


def process_move(move_san, game_data, mail):
    """Processes a move request from a user."""

    board = chess.Board()

    if game_data['pgn']:
        _board_load_pgn(board, game_data['pgn'])

    if not _attempt_move(move_san, board):
        return False

    game = chess.pgn.Game.from_board(board)

    # Since PGN data is generated from the board,
    # previous headers are lost so re-generate them.
    _regen_pgn_headers(game, game_data)

    _update_game_data(game_data, str(game).replace('\n', '\\n'),
                      _get_game_status(board))
    _update_game_db(game_data)

    _notify_player(mail, _get_game_status(board), game_data, move_san)

    return True
