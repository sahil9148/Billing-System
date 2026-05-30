"""
BillFlow Pro — AI Chatbot Routes
"""
from flask import Blueprint, request, jsonify
from database import get_db, close_db
from routes.auth import token_required
from ai_engine import BillingAssistant

chat_bp = Blueprint('chat', __name__, url_prefix='/api/chat')
assistant = BillingAssistant()


@chat_bp.route('', methods=['POST'])
@token_required
def send_message(current_user_id):
    data = request.get_json()
    message = data.get('message', '').strip()

    if not message:
        return jsonify({'error': 'Message is required'}), 400

    # Get AI response
    response = assistant.process_message(current_user_id, message)

    # Save to history
    conn = get_db()
    try:
        conn.execute("""
            INSERT INTO chat_history (user_id, message, response)
            VALUES (?, ?, ?)
        """, (current_user_id, message, response))
        conn.commit()
    finally:
        close_db(conn)

    return jsonify({'response': response}), 200


@chat_bp.route('/history', methods=['GET'])
@token_required
def get_history(current_user_id):
    conn = get_db()
    try:
        history = conn.execute("""
            SELECT message, response, created_at
            FROM chat_history WHERE user_id = ?
            ORDER BY created_at DESC LIMIT 50
        """, (current_user_id,)).fetchall()

        return jsonify([dict(h) for h in history][::-1]), 200
    finally:
        close_db(conn)
