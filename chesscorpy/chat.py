from . import constants, database, user


def get_chats(game_id):
    """ Retrieves the chat messages for a specified game. """

    query = "SELECT * FROM chats WHERE game_id = ? ORDER BY timestamp ASC"
    query_args = [game_id]

    chats = database.sql_exec(constants.DATABASE_FILE, query, query_args)
    chats = [dict(chat) for chat in chats]

    # Add username to the chat data
    for chat in chats:
        chat["user_name"] = user.get_data_by_id(chat["user_id"], ["username"])["username"]

    return chats


def new_chat(game_id, user_id, msg):
    """ Inserts a new chat message for a specified game into the database. """

    query = "INSERT INTO chats (game_id, user_id, contents) VALUES(?, ?, ?)"
    query_args = [game_id, user_id, msg]

    database.sql_exec(constants.DATABASE_FILE, query, query_args)
