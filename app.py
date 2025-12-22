from flask import Flask, render_template
from routes.main import main_bp
from routes.admin import admin_bp
import logging

app = Flask(__name__)
app.secret_key = "your-secret-key"  # セッションに必要！

# Blueprint 登録
app.register_blueprint(main_bp)
app.register_blueprint(admin_bp, url_prefix="/admin")

@app.route("/") 
def index(): return render_template("index.html")

# ルート一覧を表示（デバッグ用）
with app.app_context():
    print("登録されているルート一覧:")
    for rule in app.url_map.iter_rules():
        print(rule)

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

