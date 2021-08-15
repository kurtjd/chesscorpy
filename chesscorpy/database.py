from sqlite3 import connect, Row


def sql_exec(db, query, query_args, get_all=True, get_keys=True, get_last_row=False):
    """ Performs queries on a database. """
    # TODO: Remove get_keys option; Possibly remove get_all option too.

    db = connect(db)
    cur = db.cursor()
    cur.row_factory = Row
    data = cur.execute(query, query_args)

    data = data.fetchall() if get_all else data.fetchone()

    if get_keys and data:
        data.keys()

    last_row_id = cur.lastrowid if get_last_row else None

    db.commit()
    db.close()

    return data if not get_last_row else last_row_id
