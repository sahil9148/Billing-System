"""
BillFlow Pro — Product Catalog Routes
"""
from flask import Blueprint, request, jsonify
from database import get_db, close_db
from routes.auth import token_required
from firebase_sync import check_and_sync_resource

products_bp = Blueprint('products', __name__, url_prefix='/api/products')


@products_bp.route('', methods=['GET'])
@token_required
def list_products(current_user_id):
    conn = get_db()
    try:
        category = request.args.get('category', '')
        search = request.args.get('search', '')

        query = "SELECT * FROM products WHERE user_id = ? AND is_active = 1"
        params = [current_user_id]

        if category:
            query += " AND category = ?"
            params.append(category)
        if search:
            query += " AND (name LIKE ? OR sku LIKE ? OR description LIKE ?)"
            s = f"%{search}%"
            params.extend([s, s, s])

        query += " ORDER BY name ASC"
        products = conn.execute(query, params).fetchall()
        return jsonify([dict(p) for p in products]), 200
    finally:
        close_db(conn)


@products_bp.route('', methods=['POST'])
@token_required
def create_product(current_user_id):
    data = request.get_json()
    if not data.get('name'):
        return jsonify({'error': 'Product name is required'}), 400

    conn = get_db()
    try:
        cursor = conn.execute("""
            INSERT INTO products (user_id, name, description, unit_price,
                tax_rate, category, sku, unit)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (current_user_id, data['name'], data.get('description', ''),
              float(data.get('unit_price', 0)), float(data.get('tax_rate', 18.0)),
              data.get('category', 'General'), data.get('sku', ''),
              data.get('unit', 'unit')))
        conn.commit()

        product = conn.execute("SELECT * FROM products WHERE id = ?",
                               (cursor.lastrowid,)).fetchone()
        
        # Firebase sync
        check_and_sync_resource(current_user_id, "products", str(product["id"]), dict(product), conn)
        
        return jsonify(dict(product)), 201
    finally:
        close_db(conn)


@products_bp.route('/<int:product_id>', methods=['GET'])
@token_required
def get_product(current_user_id, product_id):
    conn = get_db()
    try:
        product = conn.execute(
            "SELECT * FROM products WHERE id = ? AND user_id = ?",
            (product_id, current_user_id)
        ).fetchone()

        if not product:
            return jsonify({'error': 'Product not found'}), 404

        return jsonify(dict(product)), 200
    finally:
        close_db(conn)


@products_bp.route('/<int:product_id>', methods=['PUT'])
@token_required
def update_product(current_user_id, product_id):
    data = request.get_json()
    conn = get_db()
    try:
        existing = conn.execute(
            "SELECT id FROM products WHERE id = ? AND user_id = ?",
            (product_id, current_user_id)
        ).fetchone()

        if not existing:
            return jsonify({'error': 'Product not found'}), 404

        conn.execute("""
            UPDATE products SET name=?, description=?, unit_price=?,
                tax_rate=?, category=?, sku=?, unit=?,
                updated_at=CURRENT_TIMESTAMP
            WHERE id = ? AND user_id = ?
        """, (data.get('name', ''), data.get('description', ''),
              float(data.get('unit_price', 0)), float(data.get('tax_rate', 18.0)),
              data.get('category', 'General'), data.get('sku', ''),
              data.get('unit', 'unit'), product_id, current_user_id))
        conn.commit()

        # Firebase sync
        product = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
        if product:
            check_and_sync_resource(current_user_id, "products", str(product_id), dict(product), conn)

        return jsonify({'message': 'Product updated successfully'}), 200
    finally:
        close_db(conn)


@products_bp.route('/<int:product_id>', methods=['DELETE'])
@token_required
def delete_product(current_user_id, product_id):
    conn = get_db()
    try:
        conn.execute(
            "UPDATE products SET is_active = 0 WHERE id = ? AND user_id = ?",
            (product_id, current_user_id)
        )
        conn.commit()
        
        # Firebase sync
        check_and_sync_resource(current_user_id, "products", str(product_id), None, conn, delete=True)
        
        return jsonify({'message': 'Product deleted successfully'}), 200
    finally:
        close_db(conn)
