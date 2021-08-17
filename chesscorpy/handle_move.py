import datetime
import chess
from . import user, database, constants, game_statuses


def update_game_db(game_data):
    """ Updates a given game in the database. """

    query = "UPDATE games SET to_move = ?, move_start_time = ?, status = ?, winner = ?, fen = ? WHERE id = ?"
    query_args = [game_data["to_move"], game_data["move_start_time"], game_data["status"], game_data["winner"],
                  game_data["fen"], game_data["id"]]

    database.sql_exec(constants.DATABASE_FILE, query, query_args)


def update_player_to_move(game_data):
    """ Set the ID of the next player to move. """

    if game_data["player_white_id"] == game_data["to_move"]:
        game_data["to_move"] = game_data["player_black_id"]
    else:
        game_data["to_move"] = game_data["player_white_id"]


def get_game_status(game):
    """ Gets the current status of a game. """

    # return game.outcome(claim_draw=True)
    return game.outcome()


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
            win_color = constants.DRAW_USER_ID

        game_data["winner"] = user.get_data_by_id(game_data[f"player_{win_color}_id"], ["id"])["id"]
    else:
        game_data["status"] = game_statuses.IN_PROGRESS


def update_game_data(game_data, game_fen, game_status):
    """ Updates the local copy of game data. """

    game_data["fen"] = game_fen
    game_data["move_start_time"] = datetime.datetime.now().replace(microsecond=0)
    update_player_to_move(game_data)
    update_game_status(game_status, game_data)


def attempt_move(move, game):
    """ Attempts to make a move if valid. """

    # TODO: Check promotion
    if move in game.legal_moves:
        game.push(move)
        return True
    else:
        return False


def process_move(move, game_data):
    """ Processes a move request from a user. """

    game = chess.Board()
    if game_data["fen"]:
        game.set_fen(game_data["fen"])

    move = chess.Move.from_uci(move)

    if not attempt_move(move, game):
        return False

    update_game_data(game_data, game.fen(), get_game_status(game))

    update_game_db(game_data)

    return True
