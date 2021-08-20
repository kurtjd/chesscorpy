from sqlite3 import connect, Row


DATABASE_FILE = "chesscorpy.db"


def sql_exec(db, query, query_args, get_all=True, get_last_row=False):
    """ Performs queries on a database. """

    db = connect(db)
    db.row_factory = Row
    cur = db.cursor()
    data = cur.execute(query, query_args)

    data = data.fetchall() if get_all else data.fetchone()

    last_row_id = cur.lastrowid if get_last_row else None

    db.commit()
    db.close()

    return data if not get_last_row else last_row_id


def row_to_dict(row):
    """ Converts a Row object into a dictionary. """

    return dict(row)


def rows_to_list(rows):
    """ Converts rows to a list of dicts. """

    return [row_to_dict(row) for row in rows]
