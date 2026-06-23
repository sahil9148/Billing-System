"""
BillFlow Pro — Invoice Management Routes
Full invoice lifecycle: create, read, update, delete, status changes, PDF generation.
"""
from flask import Blueprint, request, jsonify, send_file
from database import get_db, close_db
from routes.auth import token_required
from config import CURRENCIES
from firebase_sync import check_and_sync_resource
import io
import os

invoices_bp = Blueprint('invoices', __name__, url_prefix='/api/invoices')


def calculate_invoice_totals(items, discount=0, discount_type='percentage'):
    """Calculate subtotal, tax, discount value, and total for invoice items."""
    subtotal = 0
    tax_total = 0
    calculated_items = []

    for item in items:
        qty = float(item.get('quantity', 1))
        price = float(item.get('unit_price', 0))
        rate = float(item.get('tax_rate', 0))

        item_subtotal = qty * price
        item_tax = round(item_subtotal * rate / 100, 2)
        item_total = round(item_subtotal + item_tax, 2)

        subtotal += item_subtotal
        tax_total += item_tax

        calculated_items.append({
            'product_id': item.get('product_id'),
            'description': item.get('description', ''),
            'quantity': qty,
            'unit_price': price,
            'tax_rate': rate,
            'tax_amount': item_tax,
            'line_total': item_total,
        })

    subtotal = round(subtotal, 2)
    tax_total = round(tax_total, 2)

    if discount_type == 'percentage':
        discount_value = round(subtotal * float(discount) / 100, 2)
    else:
        discount_value = round(float(discount), 2)

    total = round(subtotal - discount_value + tax_total, 2)

    return subtotal, tax_total, discount_value, total, calculated_items


@invoices_bp.route('', methods=['GET'])
@token_required
def list_invoices(current_user_id):
    conn = get_db()
    try:
        status = request.args.get('status', '')
        client_id = request.args.get('client_id', '')
        from_date = request.args.get('from_date', '')
        to_date = request.args.get('to_date', '')
        search = request.args.get('search', '')

        query = """
            SELECT i.*, c.name as client_name, c.company as client_company
            FROM invoices i
            JOIN clients c ON c.id = i.client_id
            WHERE i.user_id = ?
        """
        params = [current_user_id]

        if status:
            query += " AND i.status = ?"
            params.append(status)
        if client_id:
            query += " AND i.client_id = ?"
            params.append(int(client_id))
        if from_date:
            query += " AND i.invoice_date >= ?"
            params.append(from_date)
        if to_date:
            query += " AND i.invoice_date <= ?"
            params.append(to_date)
        if search:
            query += " AND (i.invoice_number LIKE ? OR c.name LIKE ?)"
            s = f"%{search}%"
            params.extend([s, s])

        query += " ORDER BY i.created_at DESC"
        invoices = conn.execute(query, params).fetchall()
        return jsonify([dict(inv) for inv in invoices]), 200
    finally:
        close_db(conn)


@invoices_bp.route('', methods=['POST'])
@token_required
def create_invoice(current_user_id):
    data = request.get_json()

    if not data.get('client_id'):
        return jsonify({'error': 'Client is required'}), 400
    if not data.get('items') or len(data['items']) == 0:
        return jsonify({'error': 'At least one item is required'}), 400

    conn = get_db()
    try:
        # Get user's invoice settings
        user = conn.execute(
            "SELECT invoice_prefix, next_invoice_number FROM users WHERE id = ?",
            (current_user_id,)
        ).fetchone()

        invoice_number = f"{user['invoice_prefix']}-{user['next_invoice_number']}"

        # Calculate totals
        discount = float(data.get('discount', 0))
        discount_type = data.get('discount_type', 'percentage')
        subtotal, tax_total, disc_val, total, calc_items = calculate_invoice_totals(
            data['items'], discount, discount_type
        )

        # Create invoice
        cursor = conn.execute("""
            INSERT INTO invoices (user_id, client_id, invoice_number, invoice_date,
                due_date, status, subtotal, tax_amount, discount, discount_type,
                total_amount, amount_paid, currency, notes, terms)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (current_user_id, data['client_id'], invoice_number,
              data.get('invoice_date', ''), data.get('due_date', ''),
              'draft', subtotal, tax_total, discount, discount_type,
              total, 0, data.get('currency', 'INR'),
              data.get('notes', ''), data.get('terms', '')))

        invoice_id = cursor.lastrowid

        # Insert items
        for item in calc_items:
            conn.execute("""
                INSERT INTO invoice_items (invoice_id, product_id, description,
                    quantity, unit_price, tax_rate, tax_amount, line_total)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (invoice_id, item['product_id'], item['description'],
                  item['quantity'], item['unit_price'], item['tax_rate'],
                  item['tax_amount'], item['line_total']))

        # Increment invoice number
        conn.execute(
            "UPDATE users SET next_invoice_number = next_invoice_number + 1 WHERE id = ?",
            (current_user_id,)
        )

        conn.commit()

        # Return full invoice
        invoice = conn.execute("""
            SELECT i.*, c.name as client_name, c.company as client_company
            FROM invoices i JOIN clients c ON c.id = i.client_id
            WHERE i.id = ?
        """, (invoice_id,)).fetchone()

        items = conn.execute(
            "SELECT * FROM invoice_items WHERE invoice_id = ?",
            (invoice_id,)
        ).fetchall()

        result = dict(invoice)
        result['items'] = [dict(it) for it in items]

        # Firebase sync
        sync_data = dict(result)
        sync_data['items'] = [dict(it) for it in items]
        check_and_sync_resource(current_user_id, "invoices", str(invoice_id), sync_data, conn)

        return jsonify(result), 201
    finally:
        close_db(conn)


@invoices_bp.route('/<int:invoice_id>', methods=['GET'])
@token_required
def get_invoice(current_user_id, invoice_id):
    conn = get_db()
    try:
        invoice = conn.execute("""
            SELECT i.*, c.name as client_name, c.company as client_company,
                c.email as client_email, c.phone as client_phone,
                c.billing_address as client_address, c.city as client_city,
                c.state as client_state, c.zip_code as client_zip,
                c.gstin as client_gstin
            FROM invoices i
            JOIN clients c ON c.id = i.client_id
            WHERE i.id = ? AND i.user_id = ?
        """, (invoice_id, current_user_id)).fetchone()

        if not invoice:
            return jsonify({'error': 'Invoice not found'}), 404

        items = conn.execute("""
            SELECT ii.*, p.name as product_name
            FROM invoice_items ii
            LEFT JOIN products p ON p.id = ii.product_id
            WHERE ii.invoice_id = ?
        """, (invoice_id,)).fetchall()

        payments = conn.execute("""
            SELECT * FROM payments WHERE invoice_id = ?
            ORDER BY payment_date DESC
        """, (invoice_id,)).fetchall()

        # Get company info
        user = conn.execute(
            "SELECT company_name, company_address, company_phone, company_email, company_gstin FROM users WHERE id = ?",
            (current_user_id,)
        ).fetchone()

        result = dict(invoice)
        result['items'] = [dict(it) for it in items]
        result['payments'] = [dict(p) for p in payments]
        result['company'] = dict(user)

        return jsonify(result), 200
    finally:
        close_db(conn)


@invoices_bp.route('/<int:invoice_id>', methods=['PUT'])
@token_required
def update_invoice(current_user_id, invoice_id):
    data = request.get_json()
    conn = get_db()
    try:
        existing = conn.execute(
            "SELECT id, status FROM invoices WHERE id = ? AND user_id = ?",
            (invoice_id, current_user_id)
        ).fetchone()

        if not existing:
            return jsonify({'error': 'Invoice not found'}), 404

        if existing['status'] == 'paid':
            return jsonify({'error': 'Cannot edit a paid invoice'}), 400

        # Recalculate totals
        discount = float(data.get('discount', 0))
        discount_type = data.get('discount_type', 'percentage')
        subtotal, tax_total, disc_val, total, calc_items = calculate_invoice_totals(
            data.get('items', []), discount, discount_type
        )

        # Update invoice
        conn.execute("""
            UPDATE invoices SET client_id=?, invoice_date=?, due_date=?,
                subtotal=?, tax_amount=?, discount=?, discount_type=?,
                total_amount=?, currency=?, notes=?, terms=?,
                updated_at=CURRENT_TIMESTAMP
            WHERE id = ? AND user_id = ?
        """, (data.get('client_id'), data.get('invoice_date'),
              data.get('due_date'), subtotal, tax_total, discount,
              discount_type, total, data.get('currency', 'INR'),
              data.get('notes', ''), data.get('terms', ''),
              invoice_id, current_user_id))

        # Replace items
        conn.execute("DELETE FROM invoice_items WHERE invoice_id = ?", (invoice_id,))
        for item in calc_items:
            conn.execute("""
                INSERT INTO invoice_items (invoice_id, product_id, description,
                    quantity, unit_price, tax_rate, tax_amount, line_total)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (invoice_id, item['product_id'], item['description'],
                  item['quantity'], item['unit_price'], item['tax_rate'],
                  item['tax_amount'], item['line_total']))

        conn.commit()

        # Firebase sync
        updated_inv = conn.execute("SELECT * FROM invoices WHERE id = ?", (invoice_id,)).fetchone()
        if updated_inv:
            inv_items = conn.execute("SELECT * FROM invoice_items WHERE invoice_id = ?", (invoice_id,)).fetchall()
            inv_data = dict(updated_inv)
            inv_data['items'] = [dict(it) for it in inv_items]
            check_and_sync_resource(current_user_id, "invoices", str(invoice_id), inv_data, conn)

        return jsonify({'message': 'Invoice updated successfully'}), 200
    finally:
        close_db(conn)


@invoices_bp.route('/<int:invoice_id>', methods=['DELETE'])
@token_required
def delete_invoice(current_user_id, invoice_id):
    conn = get_db()
    try:
        conn.execute(
            "DELETE FROM invoice_items WHERE invoice_id = ?", (invoice_id,)
        )
        conn.execute(
            "DELETE FROM payments WHERE invoice_id = ?", (invoice_id,)
        )
        conn.execute(
            "DELETE FROM invoices WHERE id = ? AND user_id = ?",
            (invoice_id, current_user_id)
        )
        conn.commit()

        # Firebase sync
        check_and_sync_resource(current_user_id, "invoices", str(invoice_id), None, conn, delete=True)

        return jsonify({'message': 'Invoice deleted successfully'}), 200
    finally:
        close_db(conn)


@invoices_bp.route('/<int:invoice_id>/status', methods=['PUT'])
@token_required
def update_status(current_user_id, invoice_id):
    data = request.get_json()
    new_status = data.get('status')

    if new_status not in ['draft', 'sent', 'paid', 'partial', 'overdue', 'cancelled']:
        return jsonify({'error': 'Invalid status'}), 400

    conn = get_db()
    try:
        invoice = conn.execute(
            "SELECT * FROM invoices WHERE id = ? AND user_id = ?",
            (invoice_id, current_user_id)
        ).fetchone()

        if not invoice:
            return jsonify({'error': 'Invoice not found'}), 404

        update_fields = "status = ?, updated_at = CURRENT_TIMESTAMP"
        params = [new_status]

        if new_status == 'paid':
            update_fields = "status = ?, amount_paid = total_amount, updated_at = CURRENT_TIMESTAMP"

        params.extend([invoice_id, current_user_id])
        conn.execute(
            f"UPDATE invoices SET {update_fields} WHERE id = ? AND user_id = ?",
            params
        )
        conn.commit()

        # Firebase sync
        updated_inv = conn.execute("SELECT * FROM invoices WHERE id = ?", (invoice_id,)).fetchone()
        if updated_inv:
            inv_items = conn.execute("SELECT * FROM invoice_items WHERE invoice_id = ?", (invoice_id,)).fetchall()
            inv_data = dict(updated_inv)
            inv_data['items'] = [dict(it) for it in inv_items]
            check_and_sync_resource(current_user_id, "invoices", str(invoice_id), inv_data, conn)

        return jsonify({'message': f'Invoice marked as {new_status}'}), 200
    finally:
        close_db(conn)


@invoices_bp.route('/<int:invoice_id>/pdf', methods=['GET'])
@token_required
def generate_pdf(current_user_id, invoice_id):
    conn = get_db()
    try:
        invoice = conn.execute("""
            SELECT i.*, c.name as client_name, c.company as client_company,
                c.email as client_email, c.billing_address as client_address,
                c.city as client_city, c.state as client_state,
                c.gstin as client_gstin
            FROM invoices i
            JOIN clients c ON c.id = i.client_id
            WHERE i.id = ? AND i.user_id = ?
        """, (invoice_id, current_user_id)).fetchone()

        if not invoice:
            return jsonify({'error': 'Invoice not found'}), 404

        items = conn.execute(
            "SELECT * FROM invoice_items WHERE invoice_id = ?",
            (invoice_id,)
        ).fetchall()

        user = conn.execute(
            "SELECT * FROM users WHERE id = ?",
            (current_user_id,)
        ).fetchone()

        # Generate PDF with ReportLab
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                                leftMargin=20*mm, rightMargin=20*mm,
                                topMargin=20*mm, bottomMargin=20*mm)

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'],
                                     fontSize=24, textColor=colors.HexColor('#6c5ce7'))
        header_style = ParagraphStyle('Header', parent=styles['Normal'],
                                       fontSize=10, textColor=colors.HexColor('#555555'))
        bold_style = ParagraphStyle('Bold', parent=styles['Normal'],
                                     fontSize=10, fontName='Helvetica-Bold')

        elements = []

        # Company name
        elements.append(Paragraph(user['company_name'] or 'Your Company', title_style))
        if user['company_address']:
            elements.append(Paragraph(user['company_address'], header_style))
        if user['company_phone']:
            elements.append(Paragraph(f"Phone: {user['company_phone']}", header_style))
        if user['company_email']:
            elements.append(Paragraph(f"Email: {user['company_email']}", header_style))
        if user['company_gstin']:
            elements.append(Paragraph(f"GSTIN: {user['company_gstin']}", header_style))

        elements.append(Spacer(1, 10*mm))

        # Invoice header
        elements.append(Paragraph(f"INVOICE {invoice['invoice_number']}", styles['Heading2']))
        elements.append(Spacer(1, 5*mm))

        # Bill To + Invoice details
        currency_sym = CURRENCIES.get(invoice['currency'], {}).get('symbol', '₹')

        info_data = [
            ['Bill To:', '', 'Invoice Details:', ''],
            [invoice['client_name'], '', 'Invoice #:', invoice['invoice_number']],
            [invoice['client_company'] or '', '', 'Date:', invoice['invoice_date']],
            [invoice['client_address'] or '', '', 'Due Date:', invoice['due_date']],
            [f"{invoice['client_city'] or ''} {invoice['client_state'] or ''}", '', 'Status:', invoice['status'].upper()],
        ]
        if invoice['client_gstin']:
            info_data.append([f"GSTIN: {invoice['client_gstin']}", '', '', ''])

        info_table = Table(info_data, colWidths=[70*mm, 10*mm, 35*mm, 50*mm])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, 0), 'Helvetica-Bold'),
            ('FONTNAME', (2, 1), (2, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 8*mm))

        # Items table
        items_header = ['#', 'Description', 'Qty', 'Unit Price', 'Tax %', 'Tax Amt', 'Total']
        items_data = [items_header]
        for idx, item in enumerate(items, 1):
            items_data.append([
                str(idx),
                item['description'],
                f"{item['quantity']:.0f}" if item['quantity'] == int(item['quantity']) else f"{item['quantity']:.2f}",
                f"{currency_sym}{item['unit_price']:,.2f}",
                f"{item['tax_rate']:.0f}%",
                f"{currency_sym}{item['tax_amount']:,.2f}",
                f"{currency_sym}{item['line_total']:,.2f}",
            ])

        items_table = Table(items_data, colWidths=[10*mm, 60*mm, 15*mm, 25*mm, 15*mm, 20*mm, 25*mm])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6c5ce7')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dddddd')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f8f8')]),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(items_table)
        elements.append(Spacer(1, 5*mm))

        # Totals
        disc_label = f"Discount ({invoice['discount']}%)" if invoice['discount_type'] == 'percentage' else "Discount"
        disc_val = invoice['subtotal'] * invoice['discount'] / 100 if invoice['discount_type'] == 'percentage' else invoice['discount']

        totals_data = [
            ['', '', 'Subtotal:', f"{currency_sym}{invoice['subtotal']:,.2f}"],
            ['', '', 'Tax:', f"{currency_sym}{invoice['tax_amount']:,.2f}"],
        ]
        if invoice['discount'] > 0:
            totals_data.append(['', '', disc_label, f"-{currency_sym}{disc_val:,.2f}"])
        totals_data.append(['', '', 'TOTAL:', f"{currency_sym}{invoice['total_amount']:,.2f}"])
        if invoice['amount_paid'] > 0:
            totals_data.append(['', '', 'Paid:', f"{currency_sym}{invoice['amount_paid']:,.2f}"])
            balance = invoice['total_amount'] - invoice['amount_paid']
            totals_data.append(['', '', 'Balance Due:', f"{currency_sym}{balance:,.2f}"])

        totals_table = Table(totals_data, colWidths=[60*mm, 35*mm, 35*mm, 35*mm])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (2, -1), (2, -1), 'Helvetica-Bold'),
            ('FONTNAME', (3, -1), (3, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('LINEABOVE', (2, -1), (-1, -1), 1, colors.HexColor('#6c5ce7')),
        ]))
        elements.append(totals_table)
        elements.append(Spacer(1, 10*mm))

        # Notes and Terms
        if invoice['notes']:
            elements.append(Paragraph('Notes:', bold_style))
            elements.append(Paragraph(invoice['notes'], header_style))
            elements.append(Spacer(1, 3*mm))
        if invoice['terms']:
            elements.append(Paragraph('Terms & Conditions:', bold_style))
            elements.append(Paragraph(invoice['terms'], header_style))

        doc.build(elements)
        buffer.seek(0)

        return send_file(buffer, mimetype='application/pdf',
                         as_attachment=True,
                         download_name=f"{invoice['invoice_number']}.pdf")
    finally:
        close_db(conn)
