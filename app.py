"""
BillFlow Pro — Main Flask Application
Professional Billing System Entry Point
"""
import os
from flask import Flask, send_from_directory, make_response
from flask_cors import CORS
from database import init_db, seed_demo_data

# Import blueprints
from routes.auth import auth_bp
from routes.clients import clients_bp
from routes.products import products_bp
from routes.invoices import invoices_bp
from routes.payments import payments_bp
from routes.expenses import expenses_bp
from routes.reports import reports_bp
from routes.chat import chat_bp

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.config['SECRET_KEY'] = 'billflow-pro-secret-key-2026'
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['TEMPLATES_AUTO_RELOAD'] = True
CORS(app)


@app.after_request
def add_no_cache(response):
    """Prevent browser from caching any file during development."""
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    response.headers['Surrogate-Control'] = 'no-store'
    # Remove ETag so browser can't use If-None-Match
    if 'ETag' in response.headers:
        del response.headers['ETag']
    if 'Last-Modified' in response.headers:
        del response.headers['Last-Modified']
    return response


# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(clients_bp)
app.register_blueprint(products_bp)
app.register_blueprint(invoices_bp)
app.register_blueprint(payments_bp)
app.register_blueprint(expenses_bp)
app.register_blueprint(reports_bp)
app.register_blueprint(chat_bp)


@app.route('/')
def index():
    response = make_response(send_from_directory('static', 'index.html'))
    return response


@app.errorhandler(404)
def not_found(e):
    return {'error': 'Resource not found'}, 404


@app.errorhandler(500)
def server_error(e):
    return {'error': 'Internal server error'}, 500


if __name__ == '__main__':
    print("[+] BillFlow Pro is running at http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
