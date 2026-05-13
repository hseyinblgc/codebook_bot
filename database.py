import sqlite3


db = sqlite3.connect('data/database.db')
cr = db.cursor()


def insertdb(data):
    cr.execute(
                """
                CREATE TABLE IF NOT EXISTS request
                (telegram_id, name, github_username,
                project_name, project_summary, status)"""
    )

    cr.execute(
            """
            INSERT INTO request VALUES (?,?,?,?,?,?)
            """,
            data
            )

    db.commit()
