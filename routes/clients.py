"""
BillFlow Pro — Client Management Routes
"""
from flask import Blueprint, request, jsonify
from database import get_db, close_db
from routes.auth import token_required

clients_bp = Blueprint('clients', __name__, url_prefix='/api/clients')


@clients_bp.route('', methods=['GET'])
@token_required
def list_clients(current_user_id):
    conn = get_db()
    try:
        search = request.args.get('search', '')
        query = """
            SELECT c.*,
                COUNT(DISTINCT i.id) as invoice_count,
                COALESCE(SUM(i.total_amount), 0) as total_billed,
                COALESCE(SUM(i.amount_paid), 0) as total_paid
            FROM clients c
            LEFT JOIN invoices i ON i.client_id = c.id
            WHERE c.user_id = ? AND c.is_active = 1
        """
        params = [current_user_id]

        if search:
            query += " AND (c.name LIKE ? OR c.company LIKE ? OR c.email LIKE ?)"
            s = f"%{search}%"
            params.extend([s, s, s])

        query += " GROUP BY c.id ORDER BY c.created_at DESC"

        clients = conn.execute(query, params).fetchall()
        return jsonify([dict(c) for c in clients]), 200
    finally:
        close_db(conn)


@clients_bp.route('', methods=['POST'])
@token_required
def create_client(current_user_id):
    data = request.get_json()
    if not data.get('name'):
        return jsonify({'error': 'Client name is required'}), 400

    conn = get_db()
    try:
        cursor = conn.execute("""
            INSERT INTO clients (user_id, name, email, phone, company,
                billing_address, city, state, zip_code, country, gstin, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (current_user_id, data['name'], data.get('email', ''),
              data.get('phone', ''), data.get('company', ''),
              data.get('billing_address', ''), data.get('city', ''),
              data.get('state', ''), data.get('zip_code', ''),
              data.get('country', 'India'), data.get('gstin', ''),
              data.get('notes', '')))
        conn.commit()

        client = conn.execute("SELECT * FROM clients WHERE id = ?",
                              (cursor.lastrowid,)).fetchone()
        return jsonify(dict(client)), 201
    finally:
        close_db(conn)


@clients_bp.route('/<int:client_id>', methods=['GET'])
@token_required
def get_client(current_user_id, client_id):
    conn = get_db()
    try:
        client = conn.execute(
            "SELECT * FROM clients WHERE id = ? AND user_id = ?",
            (client_id, current_user_id)
        ).fetchone()

        if not client:
            return jsonify({'error': 'Client not found'}), 404

        invoices = conn.execute("""
            SELECT id, invoice_number, invoice_date, due_date, status,
                total_amount, amount_paid
            FROM invoices WHERE client_id = ? AND user_id = ?
            ORDER BY invoice_date DESC
        """, (client_id, current_user_id)).fetchall()

        result = dict(client)
        result['invoices'] = [dict(i) for i in invoices]
        result['total_billed'] = sum(i['total_amount'] for i in invoices)
        result['total_paid'] = sum(i['amount_paid'] for i in invoices)
        result['invoice_count'] = len(invoices)

        return jsonify(result), 200
    finally:
        close_db(conn)


@clients_bp.route('/<int:client_id>', methods=['PUT'])
@token_required
def update_client(current_user_id, client_id):
    data = request.get_json()
    conn = get_db()
    try:
        existing = conn.execute(
            "SELECT id FROM clients WHERE id = ? AND user_id = ?",
            (client_id, current_user_id)
        ).fetchone()

        if not existing:
            return jsonify({'error': 'Client not found'}), 404

        conn.execute("""
            UPDATE clients SET name=?, email=?, phone=?, company=?,
                billing_address=?, city=?, state=?, zip_code=?,
                country=?, gstin=?, notes=?, updated_at=CURRENT_TIMESTAMP
            WHERE id = ? AND user_id = ?
        """, (data.get('name', ''), data.get('email', ''),
              data.get('phone', ''), data.get('company', ''),
              data.get('billing_address', ''), data.get('city', ''),
              data.get('state', ''), data.get('zip_code', ''),
              data.get('country', 'India'), data.get('gstin', ''),
              data.get('notes', ''), client_id, current_user_id))
        conn.commit()

        return jsonify({'message': 'Client updated successfully'}), 200
    finally:
        close_db(conn)


@clients_bp.route('/<int:client_id>', methods=['DELETE'])
@token_required
def delete_client(current_user_id, client_id):
    conn = get_db()
    try:
        conn.execute(
            "UPDATE clients SET is_active = 0 WHERE id = ? AND user_id = ?",
            (client_id, current_user_id)
        )
        conn.commit()
        return jsonify({'message': 'Client deleted successfully'}), 200
    finally:
        close_db(conn)
