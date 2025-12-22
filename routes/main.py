from flask import Blueprint, render_template, request, jsonify
from datetime import datetime, timedelta
from utils.database import get_db_connection
import uuid
import configparser
import os

main_bp = Blueprint("main", __name__)

def load_config():
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__), "..", "config.ini")
    config.read(os.path.abspath(config_path))
    return config

def delete_old_logs_user(cursor, user_id):
    # 最新3件の入室ログのIDを取得
    cursor.execute("""
        SELECT id FROM Logs
        WHERE user_id = ? AND [入室日時] IS NOT NULL
        ORDER BY [入室日時] DESC
    """, (user_id,))
    rows = cursor.fetchall()
    keep_ids = [row.id for row in rows[:3]]  # 最新3件のIDだけ残す

    if keep_ids:
        placeholders = ",".join("?" for _ in keep_ids)
        sql = f"""
            DELETE FROM Logs
            WHERE user_id = ?
            AND [入室日時] IS NOT NULL
            AND id NOT IN ({placeholders})
        """
        cursor.execute(sql, (user_id, *keep_ids))
    else:
        # 3件未満なら削除しない
        pass

def is_duplicate_action(cursor, user_id, action):
    cursor.execute("SELECT status FROM Users WHERE ID = ?", (user_id,))
    result = cursor.fetchone()
    if result and result.status == action:
        return True
    return False

@main_bp.route("/")
def index():
    config = load_config()
    background_image = config["UI"].get("background_index", "images/background.jpg")
    api_url = config["API"].get("endpoint", "/entry")
    return render_template("index.html", background_image=background_image, api_url=api_url)

@main_bp.route("/status-check", methods=["GET", "POST"])
def status_check():
    config = load_config()
    background = config["UI"].get("background_status", "images/status_bg.jpg")
    result = None
    error = None

    if request.method == "POST":
        user_id = request.form.get("id", "").strip()
        if not user_id:
            error = "ユーザーIDを入力してください"
        else:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT id, name, status FROM Users WHERE id = ?", (user_id,))
            user = cursor.fetchone()

            if not user:
                error = "ユーザーが見つかりません"
            else:
                cursor.execute("""
                    SELECT TOP 1 [入室日時]
                    FROM Logs
                    WHERE user_id = ? AND [入室日時] IS NOT NULL
                    ORDER BY [入室日時] DESC
                """, (user_id,))
                in_row = cursor.fetchone()
                last_in = in_row[0] if in_row else "---"

                cursor.execute("""
                    SELECT TOP 1 [退室日時]
                    FROM Logs
                    WHERE user_id = ? AND [退室日時] IS NOT NULL
                    ORDER BY [退室日時] DESC
                """, (user_id,))
                out_row = cursor.fetchone()
                last_out = out_row[0] if out_row else "---"

                result = {
                    "id": user.id,
                    "name": user.name,
                    "status": 1 if user.status == "in" else 2,
                    "last_in": last_in,
                    "last_out": last_out
                }

            conn.close()

    return render_template("status_check.html", result=result, error=error, background=background)

@main_bp.route("/qr-entry", methods=["POST"])
def qr_entry():
    try:
        data = request.get_json()
        user_id = data.get("id")
        now = datetime.now() 
        timestamp = now.strftime("[%Y-%m-%d %H:%M:%S]")

        if not user_id:
            return jsonify({"error": "IDが送信されていません"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM Users WHERE ID = ?", (user_id,))
        user = cursor.fetchone()
        if not user:
            conn.close()
            return jsonify({"error": "IDが見つかりませんでした"}), 404

        name = user.name
        current_status = user.status or "out"
        new_status = "out" if current_status == "in" else "in"

        cursor.execute("UPDATE Users SET status = ? WHERE ID = ?", (new_status, user_id))

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if new_status == "in":
            log_id = str(uuid.uuid4())
            cursor.execute(
                "INSERT INTO Logs (id, user_id, [入室日時]) VALUES (?, ?, ?)",
                (log_id, user_id, now)
            )
            delete_old_logs_user(cursor, user_id)
        else:
            # 最新の入室ログを更新
            cursor.execute("""
                SELECT id FROM Logs
                WHERE user_id = ? AND [入室日時] IS NOT NULL AND [退室日時] IS NULL
                ORDER BY [入室日時] DESC
            """, (user_id,))
            row = cursor.fetchone()
            if row:
                cursor.execute(
                    "UPDATE Logs SET [退室日時] = ? WHERE id = ?",
                    (now, row.id)
                )
            else:
                # 念のため、退室だけのログを追加（想定外のケース）
                log_id = str(uuid.uuid4())
                cursor.execute(
                    "INSERT INTO Logs (id, user_id, [退室日時]) VALUES (?, ?, ?)",
                    (log_id, user_id, now)
                )

        conn.commit()
        conn.close()

        message = f"{timestamp} {name}さんの {'入室' if new_status == 'in' else '退室'} を記録しました"
        return jsonify({"message": message})

    except Exception as e:
        print("qr_entry エラー:", e)
        return jsonify({"error": "サーバー側でエラーが発生しました"}), 500

@main_bp.route("/manual-entry", methods=["POST"])
def manual_entry():
    try:
        data = request.get_json()
        user_id = data.get("id")
        action = data.get("action")
        now = datetime.now() 
        timestamp = now.strftime("[%Y-%m-%d %H:%M:%S]")

        if not user_id or not action:
            return jsonify({"error": "IDまたはアクションが不足しています。"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM Users WHERE ID = ?", (user_id,))
        user = cursor.fetchone()
        if not user:
            conn.close()
            return jsonify({"error": "IDが見つかりませんでした。"}), 404

        name = user.name  # ← ここで名前を取得！

        if is_duplicate_action(cursor, user_id, action): 
            conn.close()
            return jsonify({
                "error": f"{name}さんはすでに{'入室' if action == 'in' else '退室'}しています"
            }), 400

        cursor.execute("UPDATE Users SET status = ? WHERE ID = ?", (action, user_id))

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_id = str(uuid.uuid4())

        if action == "in":
            log_id = str(uuid.uuid4())
            cursor.execute(
                "INSERT INTO Logs (id, user_id, [入室日時]) VALUES (?, ?, ?)",
                (log_id, user_id, now)
            )
        else:
            # 最新の入室ログを取得
            cursor.execute("""
                SELECT id FROM Logs
                WHERE user_id = ? AND [入室日時] IS NOT NULL AND [退室日時] IS NULL
                ORDER BY [入室日時] DESC
            """, (user_id,))
            row = cursor.fetchone()

            if row:
                log_id = row.id
                cursor.execute(
                    "UPDATE Logs SET [退室日時] = ? WHERE id = ?",
                    (now, log_id)
                )
            else:
                # 入室ログが見つからない場合は新規追加（保険）
                log_id = str(uuid.uuid4())
                cursor.execute(
                    "INSERT INTO Logs (id, user_id, [退室日時]) VALUES (?, ?, ?)",
                    (log_id, user_id, now)
                )

        delete_old_logs_user(cursor, user_id)

        conn.commit()
        conn.close()

        message = f"{timestamp} {name}さんの {'入室' if action == 'in' else '退室'} を記録しました"
        return jsonify({"message": message})

    except Exception as e:
        # ログに出力しておくとデバッグしやすい！
        print("manual_entry エラー:", e)
        return jsonify({"error": "サーバー側でエラーが発生しました。"}), 500

