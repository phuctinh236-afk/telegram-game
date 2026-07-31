import os
from flask import Flask, send_from_directory, request, jsonify

app = Flask(__name__, static_folder='public', static_url_path='')

# Route chính để mở file index.html
@app.route('/')
def index():
    return send_from_directory('public', 'index.html')

# Route để phục vụ các file giao diện game khác (taixiu.html, nohu.html,...)
@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('public', path)

# API mẫu nhận dữ liệu đăng nhập / số dư từ game
@app.route('/api/auth', methods=['POST'])
def auth():
    data = request.json or {}
    return jsonify({
        "success": True,
        "user": {
            "username": data.get("username", "Player"),
            "balance": 50000
        }
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    
