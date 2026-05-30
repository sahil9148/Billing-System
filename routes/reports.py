"""
BillFlow Pro — Reports & Analytics Routes
Dashboard KPIs, revenue trends, top clients, P&L, tax summary, aging report.
"""
from flask import Blueprint, request, jsonify
from database import get_db, close_db
from routes.auth import token_required
from datetime import datetime, timedelta

reports_bp = Blueprint('reports', __name__, url_prefix='/api/reports')


@reports_bp.route('/dashboard', methods=['GET'])
@token_required
def dashboard(current_user_id):
    conn = get_db()
    try:
        now = datetime.now()
        first_of_month = now.strftime('%Y-%m-01')
        last_month_start = (now.replace(day=1) - timedelta(days=1)).strftime('%Y-%m-01')
        last_month_end = (now.replace(day=1) - timedelta(days=1)).strftime('%Y-%m-%d')

        # Total revenue (paid invoices)
        total_revenue = conn.execute("""
            SELECT COALESCE(SUM(amount_paid), 0) as total
            FROM invoices WHERE user_id = ? AND status IN ('paid', 'partial')
        """, (current_user_id,)).fetchone()['total']

        # Revenue this month
        revenue_this_month = conn.execute("""
            SELECT COALESCE(SUM(amount_paid), 0) as total
            FROM invoices WHERE user_id = ? AND status IN ('paid', 'partial')
            AND invoice_date >= ?
        """, (current_user_id, first_of_month)).fetchone()['total']

        # Revenue last month
        revenue_last_month = conn.execute("""
            SELECT COALESCE(SUM(amount_paid), 0) as total
            FROM invoices WHERE user_id = ? AND status IN ('paid', 'partial')
            AND invoice_date >= ? AND invoice_date <= ?
        """, (current_user_id, last_month_start, last_month_end)).fetchone()['total']

        # Outstanding amount
        outstanding = conn.execute("""
            SELECT COALESCE(SUM(total_amount - amount_paid), 0) as total
            FROM invoices WHERE user_id = ?
            AND status IN ('sent', 'partial', 'overdue')
        """, (current_user_id,)).fetchone()['total']

        # Total clients
        total_clients = conn.execute(
            "SELECT COUNT(*) as count FROM clients WHERE user_id = ? AND is_active = 1",
            (current_user_id,)
        ).fetchone()['count']

        # Invoices this month
        invoices_this_month = conn.execute("""
            SELECT COUNT(*) as count FROM invoices
            WHERE user_id = ? AND invoice_date >= ?
        """, (current_user_id, first_of_month)).fetchone()['count']

        # Overdue count
        today = now.strftime('%Y-%m-%d')
        overdue = conn.execute("""
            SELECT COUNT(*) as count FROM invoices
            WHERE user_id = ? AND status IN ('sent', 'partial')
            AND due_date < ?
        """, (current_user_id, today)).fetchone()['count']

        # Mark overdue invoices
        conn.execute("""
            UPDATE invoices SET status = 'overdue'
            WHERE user_id = ? AND status IN ('sent', 'partial')
            AND due_date < ?
        """, (current_user_id, today))
        conn.commit()

        # Expenses this month
        expenses_this_month = conn.execute("""
            SELECT COALESCE(SUM(amount), 0) as total FROM expenses
            WHERE user_id = ? AND expense_date >= ?
        """, (current_user_id, first_of_month)).fetchone()['total']

        # Recent invoices
        recent_invoices = conn.execute("""
            SELECT i.id, i.invoice_number, i.invoice_date, i.total_amount,
                i.status, c.name as client_name
            FROM invoices i JOIN clients c ON c.id = i.client_id
            WHERE i.user_id = ?
            ORDER BY i.created_at DESC LIMIT 5
        """, (current_user_id,)).fetchall()

        # Recent payments
        recent_payments = conn.execute("""
            SELECT p.id, p.amount, p.payment_date, p.payment_method,
                i.invoice_number, c.name as client_name
            FROM payments p
            JOIN invoices i ON i.id = p.invoice_id
            JOIN clients c ON c.id = i.client_id
            WHERE p.user_id = ?
            ORDER BY p.created_at DESC LIMIT 5
        """, (current_user_id,)).fetchall()

        # Revenue change percentage
        if revenue_last_month > 0:
            revenue_change = round((revenue_this_month - revenue_last_month) / revenue_last_month * 100, 1)
        else:
            revenue_change = 100 if revenue_this_month > 0 else 0

        return jsonify({
            'total_revenue': round(total_revenue, 2),
            'revenue_this_month': round(revenue_this_month, 2),
            'revenue_change': revenue_change,
            'outstanding': round(outstanding, 2),
            'total_clients': total_clients,
            'invoices_this_month': invoices_this_month,
            'overdue_count': overdue,
            'expenses_this_month': round(expenses_this_month, 2),
            'recent_invoices': [dict(i) for i in recent_invoices],
            'recent_payments': [dict(p) for p in recent_payments],
        }), 200
    finally:
        close_db(conn)


@reports_bp.route('/revenue', methods=['GET'])
@token_required
def revenue_report(current_user_id):
    conn = get_db()
    try:
        # Last 12 months revenue and expenses
        months_data = []
        now = datetime.now()

        for i in range(11, -1, -1):
            dt = now - timedelta(days=i * 30)
            month_start = dt.replace(day=1).strftime('%Y-%m-01')
            if dt.month == 12:
                month_end = dt.replace(year=dt.year + 1, month=1, day=1).strftime('%Y-%m-%d')
            else:
                month_end = dt.replace(month=dt.month + 1, day=1).strftime('%Y-%m-%d')

            revenue = conn.execute("""
                SELECT COALESCE(SUM(amount_paid), 0) as total
                FROM invoices WHERE user_id = ?
                AND invoice_date >= ? AND invoice_date < ?
                AND status IN ('paid', 'partial')
            """, (current_user_id, month_start, month_end)).fetchone()['total']

            expenses = conn.execute("""
                SELECT COALESCE(SUM(amount), 0) as total
                FROM expenses WHERE user_id = ?
                AND expense_date >= ? AND expense_date < ?
            """, (current_user_id, month_start, month_end)).fetchone()['total']

            months_data.append({
                'month': dt.strftime('%b %Y'),
                'revenue': round(revenue, 2),
                'expenses': round(expenses, 2),
                'profit': round(revenue - expenses, 2)
            })

        return jsonify(months_data), 200
    finally:
        close_db(conn)


@reports_bp.route('/top-clients', methods=['GET'])
@token_required
def top_clients(current_user_id):
    conn = get_db()
    try:
        clients = conn.execute("""
            SELECT c.name, c.company,
                COALESCE(SUM(i.total_amount), 0) as total_billed,
                COALESCE(SUM(i.amount_paid), 0) as total_paid,
                COUNT(i.id) as invoice_count
            FROM clients c
            LEFT JOIN invoices i ON i.client_id = c.id
            WHERE c.user_id = ? AND c.is_active = 1
            GROUP BY c.id
            ORDER BY total_billed DESC
            LIMIT 5
        """, (current_user_id,)).fetchall()

        return jsonify([dict(c) for c in clients]), 200
    finally:
        close_db(conn)


@reports_bp.route('/profit-loss', methods=['GET'])
@token_required
def profit_loss(current_user_id):
    conn = get_db()
    try:
        now = datetime.now()
        first_of_month = now.strftime('%Y-%m-01')
        first_of_year = now.strftime('%Y-01-01')

        # This month
        month_revenue = conn.execute("""
            SELECT COALESCE(SUM(amount_paid), 0) as total FROM invoices
            WHERE user_id = ? AND invoice_date >= ? AND status IN ('paid', 'partial')
        """, (current_user_id, first_of_month)).fetchone()['total']

        month_expenses = conn.execute("""
            SELECT COALESCE(SUM(amount), 0) as total FROM expenses
            WHERE user_id = ? AND expense_date >= ?
        """, (current_user_id, first_of_month)).fetchone()['total']

        # This year
        year_revenue = conn.execute("""
            SELECT COALESCE(SUM(amount_paid), 0) as total FROM invoices
            WHERE user_id = ? AND invoice_date >= ? AND status IN ('paid', 'partial')
        """, (current_user_id, first_of_year)).fetchone()['total']

        year_expenses = conn.execute("""
            SELECT COALESCE(SUM(amount), 0) as total FROM expenses
            WHERE user_id = ? AND expense_date >= ?
        """, (current_user_id, first_of_year)).fetchone()['total']

        return jsonify({
            'month': {
                'revenue': round(month_revenue, 2),
                'expenses': round(month_expenses, 2),
                'profit': round(month_revenue - month_expenses, 2),
                'period': now.strftime('%B %Y')
            },
            'year': {
                'revenue': round(year_revenue, 2),
                'expenses': round(year_expenses, 2),
                'profit': round(year_revenue - year_expenses, 2),
                'period': now.strftime('%Y')
            }
        }), 200
    finally:
        close_db(conn)


@reports_bp.route('/tax-summary', methods=['GET'])
@token_required
def tax_summary(current_user_id):
    conn = get_db()
    try:
        taxes = conn.execute("""
            SELECT ii.tax_rate,
                SUM(ii.tax_amount) as total_tax,
                SUM(ii.quantity * ii.unit_price) as taxable_amount,
                COUNT(DISTINCT ii.invoice_id) as invoice_count
            FROM invoice_items ii
            JOIN invoices i ON i.id = ii.invoice_id
            WHERE i.user_id = ? AND i.status IN ('paid', 'partial', 'sent')
            GROUP BY ii.tax_rate
            ORDER BY ii.tax_rate
        """, (current_user_id,)).fetchall()

        total_tax = sum(t['total_tax'] for t in taxes)

        return jsonify({
            'breakdown': [dict(t) for t in taxes],
            'total_tax': round(total_tax, 2)
        }), 200
    finally:
        close_db(conn)


@reports_bp.route('/aging', methods=['GET'])
@token_required
def aging_report(current_user_id):
    conn = get_db()
    try:
        today = datetime.now().strftime('%Y-%m-%d')

        aging = {
            'current': {'count': 0, 'amount': 0},
            '1_30': {'count': 0, 'amount': 0},
            '31_60': {'count': 0, 'amount': 0},
            '61_90': {'count': 0, 'amount': 0},
            '90_plus': {'count': 0, 'amount': 0},
        }

        invoices = conn.execute("""
            SELECT due_date, total_amount, amount_paid
            FROM invoices WHERE user_id = ?
            AND status IN ('sent', 'partial', 'overdue')
        """, (current_user_id,)).fetchall()

        for inv in invoices:
            balance = inv['total_amount'] - inv['amount_paid']
            if balance <= 0:
                continue

            due = datetime.strptime(inv['due_date'], '%Y-%m-%d')
            days_overdue = (datetime.strptime(today, '%Y-%m-%d') - due).days

            if days_overdue <= 0:
                aging['current']['count'] += 1
                aging['current']['amount'] += balance
            elif days_overdue <= 30:
                aging['1_30']['count'] += 1
                aging['1_30']['amount'] += balance
            elif days_overdue <= 60:
                aging['31_60']['count'] += 1
                aging['31_60']['amount'] += balance
            elif days_overdue <= 90:
                aging['61_90']['count'] += 1
                aging['61_90']['amount'] += balance
            else:
                aging['90_plus']['count'] += 1
                aging['90_plus']['amount'] += balance

        # Round amounts
        for key in aging:
            aging[key]['amount'] = round(aging[key]['amount'], 2)

        return jsonify(aging), 200
    finally:
        close_db(conn)
