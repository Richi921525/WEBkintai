from flask import Blueprint, render_template, request, session, redirect, url_for
from utils.database import get_db_connection
import configparser
import os

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

def load_config():
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__), "..", "config.ini")
    config.read(os.path.abspath(config_path))
    return config

@admin_bp.route("/login", methods=["GET", "POST"])
def admin_login():

    config = load_config()
    background = config["UI"].get("background_login") or "images/login_bg.jpg"
    error = None

    if request.method == "POST":
        admin_id = request.form.get("id", "").strip()
        password = request.form.get("password", "").strip()

        if not admin_id or not password:
            error = "IDとパスワードを入力してください"
        else:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT id, password FROM Admins WHERE id = ?", (admin_id,))
            admin = cursor.fetchone()

            if not admin:
                error = "管理者IDが見つかりません"
            else:
                if str(admin["password"]).strip() != password:
                    print("パスワードが一致しません")
                    error = "パスワードが正しくありません"
                else:
                    session["admin_logged_in"] = True
                    session["admin_id"] = admin_id
                    conn.close()
                    return redirect(url_for("admin.admin_page"))

            conn.close()

    return render_template("admin_login.html", background=background, error=error)

@admin_bp.route("/")
def admin_page():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin.admin_login"))

    config = load_config()
    background = config["UI"].get("background_admin") or "images/admin_bg.jpg"
    register_message = session.pop("register_message", None)

    return render_template("admin.html", background=background, register_message=register_message)

@admin_bp.route("/register", methods=["POST"])
def register_user():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin.admin_login"))

    new_id = request.form.get("new_id", "").strip()
    new_name = request.form.get("new_name", "").strip()

    if not new_id or not new_name:
        session["register_message"] = "IDと名前を入力してください"
        return redirect(url_for("admin.admin_page"))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM Users WHERE id = ?", (new_id,))
    if cursor.fetchone():
        session["register_message"] = "そのIDはすでに登録されています"
    else:
        # status を省略して登録（NULLになる）
        cursor.execute("INSERT INTO Users (id, name) VALUES (?, ?)", (new_id, new_name))
        conn.commit()
        session["register_message"] = f"{new_name} さんを登録しました"

    conn.close()
    return redirect(url_for("admin.admin_page"))

@admin_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("main.index"))  # トップページに戻る

