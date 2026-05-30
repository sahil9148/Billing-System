"""
BillFlow Pro — Expense Management Routes
"""
from flask import Blueprint, request, jsonify
from database import get_db, close_db
from routes.auth import token_required

expenses_bp = Blueprint('expenses', __name__, url_prefix='/api/expenses')


@expenses_bp.route('', methods=['GET'])
@token_required
def list_expenses(current_user_id):
    conn = get_db()
    try:
        category = request.args.get('category', '')
        from_date = request.args.get('from_date', '')
        to_date = request.args.get('to_date', '')
        search = request.args.get('search', '')

        query = "SELECT * FROM expenses WHERE user_id = ?"
        params = [current_user_id]

        if category:
            query += " AND category = ?"
            params.append(category)
        if from_date:
            query += " AND expense_date >= ?"
            params.append(from_date)
        if to_date:
            query += " AND expense_date <= ?"
            params.append(to_date)
        if search:
            query += " AND (description LIKE ? OR vendor LIKE ?)"
            s = f"%{search}%"
            params.extend([s, s])

        query += " ORDER BY expense_date DESC"
        expenses = conn.execute(query, params).fetchall()

        # Category summary
        summary = conn.execute("""
            SELECT category, SUM(amount) as total, COUNT(*) as count
            FROM expenses WHERE user_id = ?
            GROUP BY category ORDER BY total DESC
        """, (current_user_id,)).fetchall()

        return jsonify({
            'expenses': [dict(e) for e in expenses],
            'summary': [dict(s) for s in summary],
            'total': sum(e['amount'] for e in expenses)
        }), 200
    finally:
        close_db(conn)


@expenses_bp.route('', methods=['POST'])
@token_required
def create_expense(current_user_id):
    data = request.get_json()
    if not data.get('amount') or not data.get('expense_date'):
        return jsonify({'error': 'Amount and date are required'}), 400

    conn = get_db()
    try:
        cursor = conn.execute("""
            INSERT INTO expenses (user_id, category, description, amount,
                expense_date, vendor, payment_method, is_billable,
                client_id, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (current_user_id, data.get('category', 'Miscellaneous'),
              data.get('description', ''), float(data['amount']),
              data['expense_date'], data.get('vendor', ''),
              data.get('payment_method', 'Cash'),
              int(data.get('is_billable', 0)),
              data.get('client_id') or None,
              data.get('notes', '')))
        conn.commit()

        expense = conn.execute("SELECT * FROM expenses WHERE id = ?",
                               (cursor.lastrowid,)).fetchone()
        return jsonify(dict(expense)), 201
    finally:
        close_db(conn)


@expenses_bp.route('/<int:expense_id>', methods=['GET'])
@token_required
def get_expense(current_user_id, expense_id):
    conn = get_db()
    try:
        expense = conn.execute(
            "SELECT * FROM expenses WHERE id = ? AND user_id = ?",
            (expense_id, current_user_id)
        ).fetchone()

        if not expense:
            return jsonify({'error': 'Expense not found'}), 404

        return jsonify(dict(expense)), 200
    finally:
        close_db(conn)


@expenses_bp.route('/<int:expense_id>', methods=['PUT'])
@token_required
def update_expense(current_user_id, expense_id):
    data = request.get_json()
    conn = get_db()
    try:
        existing = conn.execute(
            "SELECT id FROM expenses WHERE id = ? AND user_id = ?",
            (expense_id, current_user_id)
        ).fetchone()

        if not existing:
            return jsonify({'error': 'Expense not found'}), 404

        conn.execute("""
            UPDATE expenses SET category=?, description=?, amount=?,
                expense_date=?, vendor=?, payment_method=?,
                is_billable=?, client_id=?, notes=?,
                updated_at=CURRENT_TIMESTAMP
            WHERE id = ? AND user_id = ?
        """, (data.get('category', 'Miscellaneous'),
              data.get('description', ''), float(data.get('amount', 0)),
              data.get('expense_date', ''), data.get('vendor', ''),
              data.get('payment_method', 'Cash'),
              int(data.get('is_billable', 0)),
              data.get('client_id') or None,
              data.get('notes', ''), expense_id, current_user_id))
        conn.commit()

        return jsonify({'message': 'Expense updated successfully'}), 200
    finally:
        close_db(conn)


@expenses_bp.route('/<int:expense_id>', methods=['DELETE'])
@token_required
def delete_expense(current_user_id, expense_id):
    conn = get_db()
    try:
        conn.execute(
            "DELETE FROM expenses WHERE id = ? AND user_id = ?",
            (expense_id, current_user_id)
        )
        conn.commit()
        return jsonify({'message': 'Expense deleted successfully'}), 200
    finally:
        close_db(conn)
