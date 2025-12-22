import configparser
import pyodbc
import os

def get_db_connection():
    # config.ini から DB パスを取得（セクション名に注意！）
    config = configparser.ConfigParser()
    config.read("config.ini")

    db_path = config["DB"].get("path", "db/Users.accdb")
    abs_path = os.path.abspath(db_path)

    conn_str = (
        r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};"
        f"DBQ={abs_path};"
    )

    conn = pyodbc.connect(conn_str)
    conn.setdecoding(pyodbc.SQL_CHAR, encoding='cp932')
    conn.setdecoding(pyodbc.SQL_WCHAR, encoding='cp932')
    conn.setencoding(encoding='cp932')

    return conn
