import os
from flask import Flask, send_from_directory, request, jsonify

app = Flask(__name__, static_folder='public')

# Route chính để mở file index.html
@app.route('/')
def index():
    return send_from_directory('public', 'index.html')

# Các trang game khác
@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('public', path)

# API đăng nhập/lấy số dư mẫu
@app.route('/api/auth', methods=['POST'])
def auth():
    data = request.json
    # Xử lý database ở đây (tạm thời trả về dữ liệu mẫu)
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
