import configparser
import sqlite3
import os

def get_db_connection():
    # config.ini から DB パスを取得（セクション名に注意！）
    config = configparser.ConfigParser()
    config.read("config.ini")

    db_path = config["DB"].get("path", "db/Users.sqlite") 
    abs_path = os.path.abspath(db_path)

    conn = sqlite3.connect(abs_path)
    conn.row_factory = sqlite3.Row

    return conn
