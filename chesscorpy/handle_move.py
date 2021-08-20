import datetime
import io
import chess
import chess.pgn
from . import user, database, constants, game_statuses


def update_game_db(game_data):
    """ Updates a given game in the database. """

    query = "UPDATE games SET to_move = ?, move_start_time = ?, status = ?, winner = ?, pgn = ? WHERE id = ?"
    query_args = [game_data["to_move"], game_data["move_start_time"], game_data["status"], game_data["winner"],
                  game_data["pgn"], game_data["id"]]

    database.sql_exec(constants.DATABASE_FILE, query, query_args)


def update_player_to_move(game_data):
    """ Set the ID of the next player to move. """

    if game_data["player_white_id"] == game_data["to_move"]:
        game_data["to_move"] = game_data["player_black_id"]
    else:
        game_data["to_move"] = game_data["player_white_id"]


def get_game_status(game):
    """ Gets the current status of a game. """

    return game.outcome(claim_draw=True)


def update_game_status(game_status, game_data):
    """ Updates the status and result of the game. """

    if game_status:
        status_options = {
            game_status.termination.CHECKMATE: game_statuses.CHECKMATE,
            game_status.termination.STALEMATE: game_statuses.STALEMATE,
            game_status.termination.INSUFFICIENT_MATERIAL: game_statuses.DRAW,
            game_status.termination.THREEFOLD_REPETITION: game_statuses.DRAW
        }

        game_data["status"] = status_options[game_status.termination]

        if game_status.winner == chess.WHITE:
            win_color = "white"
        elif game_status.winner == chess.BLACK:
            win_color = "black"
        else:
            win_color = None

        if win_color:
            game_data["winner"] = user.get_data_by_id(game_data[f"player_{win_color}_id"], ["id"])["id"]
        else:
            game_data["winner"] = constants.DRAW_USER_ID
    else:
        game_data["status"] = game_statuses.IN_PROGRESS


def update_game_data(game_data, game_pgn, game_status):
    """ Updates the local copy of game data. """

    game_data["pgn"] = game_pgn
    game_data["move_start_time"] = datetime.datetime.now().replace(microsecond=0)
    update_player_to_move(game_data)
    update_game_status(game_status, game_data)


def attempt_move(move_san, game):
    """ Attempts to make a move if valid. """

    move = game.parse_san(move_san)
    if move in game.legal_moves:
        game.push(move)
        return True
    else:
        return False


def regen_pgn_headers(game, game_data):
    """ Regenerates the PGN headers for the game. """

    game.headers["Event"] = "Correspondence Chess"
    game.headers["Site"] = "ChessCorPy"
    game.headers["Date"] = datetime.datetime.strptime(game_data["timestamp"], "%Y-%m-%d %H:%M:%S").strftime("%Y.%m.%d")
    game.headers["Round"] = '-'
    game.headers["White"] = user.get_data_by_id(game_data[f"player_white_id"], ["username"])["username"]
    game.headers["Black"] = user.get_data_by_id(game_data[f"player_black_id"], ["username"])["username"]


def board_load_pgn(board, pgn):
    """ Loads pgn into a board. """

    game = chess.pgn.read_game(io.StringIO(pgn))
    for move in game.mainline_moves():
        board.push(move)


def process_move(move_san, game_data):
    """ Processes a move request from a user. """

    board = chess.Board()

    if game_data["pgn"]:
        board_load_pgn(board, game_data["pgn"])

    if not attempt_move(move_san, board):
        return False

    game = chess.pgn.Game.from_board(board)

    # Since PGN data is generated from the board, previous headers are lost so re-generate them.
    regen_pgn_headers(game, game_data)

    update_game_data(game_data, str(game).replace('\n', "\\n"), get_game_status(board))
    update_game_db(game_data)

    return True
