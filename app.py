from flask import Flask
from routes.main import main_bp
from routes.admin import admin_bp
import logging

app = Flask(__name__)
app.secret_key = "your-secret-key"  # セッションに必要！

# Blueprint 登録
app.register_blueprint(main_bp)
app.register_blueprint(admin_bp, url_prefix="/admin")

# ルート一覧を表示（デバッグ用）
with app.app_context():
    print("登録されているルート一覧:")
    for rule in app.url_map.iter_rules():
        print(rule)

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    app.run(host="0.0.0.0", port=8000, debug=True)
