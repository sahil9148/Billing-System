"""
BillFlow Pro — Authentication Routes
Handles login, registration, profile management with JWT tokens.
"""
from flask import Blueprint, request, jsonify
import jwt
import bcrypt
import datetime
from functools import wraps
from config import SECRET_KEY, JWT_EXPIRATION_HOURS
from database import get_db, close_db

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


def token_required(f):
    """Decorator to protect routes with JWT authentication."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]

        if not token:
            return jsonify({'error': 'Authentication token is missing'}), 401

        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            current_user_id = data['user_id']
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401

        return f(current_user_id, *args, **kwargs)
    return decorated


def generate_token(user_id):
    """Generate a JWT token for the given user."""
    payload = {
        'user_id': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=JWT_EXPIRATION_HOURS),
        'iat': datetime.datetime.utcnow()
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password are required'}), 400

    conn = get_db()
    try:
        user = conn.execute(
            "SELECT * FROM users WHERE username = ? AND is_active = 1",
            (data['username'],)
        ).fetchone()

        if not user:
            return jsonify({'error': 'Invalid username or password'}), 401

        if not bcrypt.checkpw(data['password'].encode('utf-8'),
                              user['password_hash'].encode('utf-8')):
            return jsonify({'error': 'Invalid username or password'}), 401

        token = generate_token(user['id'])

        return jsonify({
            'token': token,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'full_name': user['full_name'],
                'role': user['role'],
                'company_name': user['company_name'],
                'default_currency': user['default_currency'],
            }
        }), 200
    finally:
        close_db(conn)


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    required = ['username', 'email', 'password']
    for field in required:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400

    if len(data['password']) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400

    conn = get_db()
    try:
        existing = conn.execute(
            "SELECT id FROM users WHERE username = ? OR email = ?",
            (data['username'], data['email'])
        ).fetchone()

        if existing:
            return jsonify({'error': 'Username or email already exists'}), 409

        pw_hash = bcrypt.hashpw(data['password'].encode('utf-8'),
                                bcrypt.gensalt()).decode('utf-8')

        cursor = conn.execute("""
            INSERT INTO users (username, email, password_hash, full_name, company_name)
            VALUES (?, ?, ?, ?, ?)
        """, (data['username'], data['email'], pw_hash,
              data.get('full_name', ''), data.get('company_name', '')))

        conn.commit()
        token = generate_token(cursor.lastrowid)

        return jsonify({
            'message': 'Account created successfully',
            'token': token,
            'user': {
                'id': cursor.lastrowid,
                'username': data['username'],
                'email': data['email'],
                'full_name': data.get('full_name', ''),
                'role': 'admin',
                'company_name': data.get('company_name', ''),
                'default_currency': 'INR',
            }
        }), 201
    finally:
        close_db(conn)


@auth_bp.route('/profile', methods=['GET'])
@token_required
def get_profile(current_user_id):
    conn = get_db()
    try:
        user = conn.execute("SELECT * FROM users WHERE id = ?",
                            (current_user_id,)).fetchone()
        if not user:
            return jsonify({'error': 'User not found'}), 404

        return jsonify({
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'full_name': user['full_name'],
            'role': user['role'],
            'company_name': user['company_name'],
            'company_address': user['company_address'],
            'company_phone': user['company_phone'],
            'company_email': user['company_email'],
            'company_gstin': user['company_gstin'],
            'company_logo': user['company_logo'],
            'default_currency': user['default_currency'],
            'default_tax_rate': user['default_tax_rate'],
            'invoice_prefix': user['invoice_prefix'],
            'next_invoice_number': user['next_invoice_number'],
            'payment_terms': user['payment_terms'],
        }), 200
    finally:
        close_db(conn)


@auth_bp.route('/profile', methods=['PUT'])
@token_required
def update_profile(current_user_id):
    data = request.get_json()
    conn = get_db()
    try:
        fields = []
        values = []
        updatable = [
            'full_name', 'email', 'company_name', 'company_address',
            'company_phone', 'company_email', 'company_gstin',
            'default_currency', 'default_tax_rate', 'invoice_prefix',
            'next_invoice_number', 'payment_terms'
        ]

        for field in updatable:
            if field in data:
                fields.append(f"{field} = ?")
                values.append(data[field])

        if data.get('password'):
            if len(data['password']) < 6:
                return jsonify({'error': 'Password must be at least 6 characters'}), 400
            pw_hash = bcrypt.hashpw(data['password'].encode('utf-8'),
                                    bcrypt.gensalt()).decode('utf-8')
            fields.append("password_hash = ?")
            values.append(pw_hash)

        if not fields:
            return jsonify({'error': 'No fields to update'}), 400

        fields.append("updated_at = CURRENT_TIMESTAMP")
        values.append(current_user_id)

        conn.execute(
            f"UPDATE users SET {', '.join(fields)} WHERE id = ?",
            values
        )
        conn.commit()

        return jsonify({'message': 'Profile updated successfully'}), 200
    finally:
        close_db(conn)
