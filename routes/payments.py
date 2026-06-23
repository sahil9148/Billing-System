"""
BillFlow Pro — Payment Tracking Routes
"""
from flask import Blueprint, request, jsonify
from database import get_db, close_db
from routes.auth import token_required
from firebase_sync import check_and_sync_resource

payments_bp = Blueprint('payments', __name__, url_prefix='/api/payments')


@payments_bp.route('', methods=['GET'])
@token_required
def list_payments(current_user_id):
    conn = get_db()
    try:
        invoice_id = request.args.get('invoice_id', '')

        query = """
            SELECT p.*, i.invoice_number, c.name as client_name
            FROM payments p
            JOIN invoices i ON i.id = p.invoice_id
            JOIN clients c ON c.id = i.client_id
            WHERE p.user_id = ?
        """
        params = [current_user_id]

        if invoice_id:
            query += " AND p.invoice_id = ?"
            params.append(int(invoice_id))

        query += " ORDER BY p.payment_date DESC"
        payments = conn.execute(query, params).fetchall()
        return jsonify([dict(p) for p in payments]), 200
    finally:
        close_db(conn)


@payments_bp.route('', methods=['POST'])
@token_required
def create_payment(current_user_id):
    data = request.get_json()

    if not data.get('invoice_id') or not data.get('amount'):
        return jsonify({'error': 'Invoice and amount are required'}), 400

    conn = get_db()
    try:
        invoice = conn.execute(
            "SELECT * FROM invoices WHERE id = ? AND user_id = ?",
            (data['invoice_id'], current_user_id)
        ).fetchone()

        if not invoice:
            return jsonify({'error': 'Invoice not found'}), 404

        amount = float(data['amount'])
        if amount <= 0:
            return jsonify({'error': 'Amount must be positive'}), 400

        # Record payment
        cursor = conn.execute("""
            INSERT INTO payments (invoice_id, user_id, payment_date, amount,
                payment_method, reference_number, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (data['invoice_id'], current_user_id,
              data.get('payment_date', ''), amount,
              data.get('payment_method', 'Cash'),
              data.get('reference_number', ''),
              data.get('notes', '')))

        # Update invoice paid amount and status
        new_paid = invoice['amount_paid'] + amount
        if new_paid >= invoice['total_amount']:
            new_status = 'paid'
            new_paid = invoice['total_amount']
        elif new_paid > 0:
            new_status = 'partial'
        else:
            new_status = invoice['status']

        conn.execute("""
            UPDATE invoices SET amount_paid = ?, status = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (round(new_paid, 2), new_status, data['invoice_id']))

        conn.commit()

        payment = conn.execute("""
            SELECT p.*, i.invoice_number, c.name as client_name
            FROM payments p
            JOIN invoices i ON i.id = p.invoice_id
            JOIN clients c ON c.id = i.client_id
            WHERE p.id = ?
        """, (cursor.lastrowid,)).fetchone()

        # Firebase sync
        check_and_sync_resource(current_user_id, "payments", str(payment["id"]), dict(payment), conn)
        
        # Also sync the updated invoice
        updated_invoice = conn.execute("SELECT * FROM invoices WHERE id = ?", (data['invoice_id'],)).fetchone()
        if updated_invoice:
            inv_data = dict(updated_invoice)
            items = conn.execute("SELECT * FROM invoice_items WHERE invoice_id = ?", (updated_invoice["id"],)).fetchall()
            inv_data["items"] = [dict(item) for item in items]
            check_and_sync_resource(current_user_id, "invoices", str(updated_invoice["id"]), inv_data, conn)

        return jsonify(dict(payment)), 201
    finally:
        close_db(conn)


@payments_bp.route('/<int:payment_id>', methods=['GET'])
@token_required
def get_payment(current_user_id, payment_id):
    conn = get_db()
    try:
        payment = conn.execute("""
            SELECT p.*, i.invoice_number, i.total_amount, i.amount_paid as invoice_paid,
                c.name as client_name
            FROM payments p
            JOIN invoices i ON i.id = p.invoice_id
            JOIN clients c ON c.id = i.client_id
            WHERE p.id = ? AND p.user_id = ?
        """, (payment_id, current_user_id)).fetchone()

        if not payment:
            return jsonify({'error': 'Payment not found'}), 404

        return jsonify(dict(payment)), 200
    finally:
        close_db(conn)


@payments_bp.route('/<int:payment_id>', methods=['DELETE'])
@token_required
def delete_payment(current_user_id, payment_id):
    conn = get_db()
    try:
        payment = conn.execute(
            "SELECT * FROM payments WHERE id = ? AND user_id = ?",
            (payment_id, current_user_id)
        ).fetchone()

        if not payment:
            return jsonify({'error': 'Payment not found'}), 404

        # Delete payment
        conn.execute("DELETE FROM payments WHERE id = ?", (payment_id,))

        # Recalculate invoice totals
        total_paid = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) as total FROM payments WHERE invoice_id = ?",
            (payment['invoice_id'],)
        ).fetchone()['total']

        invoice = conn.execute(
            "SELECT total_amount FROM invoices WHERE id = ?",
            (payment['invoice_id'],)
        ).fetchone()

        if total_paid >= invoice['total_amount']:
            status = 'paid'
        elif total_paid > 0:
            status = 'partial'
        else:
            status = 'sent'

        conn.execute("""
            UPDATE invoices SET amount_paid = ?, status = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (round(total_paid, 2), status, payment['invoice_id']))

        conn.commit()

        # Firebase sync
        check_and_sync_resource(current_user_id, "payments", str(payment_id), None, conn, delete=True)
        
        # Also sync the updated invoice
        updated_invoice = conn.execute("SELECT * FROM invoices WHERE id = ?", (payment['invoice_id'],)).fetchone()
        if updated_invoice:
            inv_data = dict(updated_invoice)
            items = conn.execute("SELECT * FROM invoice_items WHERE invoice_id = ?", (updated_invoice["id"],)).fetchall()
            inv_data["items"] = [dict(item) for item in items]
            check_and_sync_resource(current_user_id, "invoices", str(updated_invoice["id"]), inv_data, conn)

        return jsonify({'message': 'Payment deleted successfully'}), 200
    finally:
        close_db(conn)
