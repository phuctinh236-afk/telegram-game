import os
import requests
from flask import Flask, send_from_directory, request, jsonify

app = Flask(__name__, static_folder='public', static_url_path='')

# CẤU HÌNH BOT TELEGRAM
BOT_TOKEN = "8576597700:AAG6p0YhWf1-QXMwR1vNtHxx6r7eAFxvRFU"
ADMIN_CHAT_ID = "8655162823"
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

# BỘ NHỚ TẠM QUẢN LÝ TIN NHẮN & PHIÊN CHAT CSKH
message_queue = {}   # { 'USER_1234': ['msg1', 'msg2'] }
closed_sessions = {} # { 'USER_1234': True/False }
reply_mapping = {}   # { message_id_telegram: 'USER_1234' }

# ==================== ROUTE STATIC & GAME ====================

@app.route('/')
def index():
    return send_from_directory('public', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('public', path)

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

# ==================== API CSKH TELEGRAM ====================

# 1. Khách gửi tin từ Web -> Bắn thông báo về Telegram Admin kèm đầy đủ ID
@app.route('/api/send-message', methods=['POST'])
def send_message():
    data = request.json or {}
    user_id = data.get('userId')
    message = data.get('message')

    if not user_id or not message:
        return jsonify({'status': 'error', 'message': 'Thiếu dữ liệu'}), 400

    if closed_sessions.get(user_id):
        return jsonify({'status': 'closed', 'message': 'Phiên chat đã bị đóng.'})

    text_content = f"💬 *TIN NHẮN CSKH MỚI*\n👤 *Khách:* `{user_id}`\n\nNội dung: \"{message}\""
    
    try:
        res = requests.post(f"{TELEGRAM_API}/sendMessage", json={
            "chat_id": ADMIN_CHAT_ID,
            "text": text_content,
            "parse_mode": "Markdown"
        }).json()

        if res.get('ok'):
            msg_id = res['result']['message_id']
            reply_mapping[msg_id] = user_id

        return jsonify({'status': 'success'})
    except Exception as e:
        print(f"Lỗi gửi Telegram: {e}")
        return jsonify({'status': 'error'}), 500

# 2. Web gọi liên tục để nhận phản hồi từ Admin
@app.route('/api/get-messages', methods=['GET'])
def get_messages():
    user_id = request.args.get('userId')

    if closed_sessions.get(user_id):
        return jsonify({'status': 'closed', 'messages': []})

    msgs = message_queue.get(user_id, [])
    message_queue[user_id] = [] # Xóa sau khi đã gửi xuống web

    return jsonify({'status': 'active', 'messages': msgs})

# 3. Webhook nhận lệnh từ Telegram (Admin Reply hoặc gõ /stop ID)
@app.route('/telegram-webhook', methods=['POST'])
def telegram_webhook():
    update = request.json or {}

    if 'message' in update:
        msg = update['message']
        text = msg.get('text', '')

        # Lệnh đóng chat: /stop USER_1234
        if text.startswith('/stop'):
            parts = text.split(' ')
            if len(parts) >= 2:
                target_user = parts[1].strip().replace('@', '')
                closed_sessions[target_user] = True
                
                requests.post(f"{TELEGRAM_API}/sendMessage", json={
                    "chat_id": ADMIN_CHAT_ID,
                    "text": f"🔒 Đã đóng phiên chat của khách: `{target_user}`",
                    "parse_mode": "Markdown"
                })
            else:
                requests.post(f"{TELEGRAM_API}/sendMessage", json={
                    "chat_id": ADMIN_CHAT_ID,
                    "text": "⚠️ Sai cú pháp! Gõ: `/stop ID_KHÁCH`",
                    "parse_mode": "Markdown"
                })
            return jsonify({'status': 'ok'})

        # Admin dùng tính năng Reply để trả lời khách
        if 'reply_to_message' in msg:
            parent_msg_id = msg['reply_to_message']['message_id']
            target_user = reply_mapping.get(parent_msg_id)

            if target_user:
                if closed_sessions.get(target_user):
                    requests.post(f"{TELEGRAM_API}/sendMessage", json={
                        "chat_id": ADMIN_CHAT_ID,
                        "text": f"⚠️ Phiên chat của khách `{target_user}` đã bị đóng!",
                        "parse_mode": "Markdown"
                    })
                else:
                    if target_user not in message_queue:
                        message_queue[target_user] = []
                    message_queue[target_user].append(text)

    return jsonify({'status': 'ok'})

# ==================== RUN SERVER ====================
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    
