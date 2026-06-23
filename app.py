import sys
import traceback

class FallbackApp:
    def __init__(self, tb_str):
        self.tb_str = tb_str

    def __call__(self, environ, start_response):
        status = '500 Internal Server Error'
        headers = [('Content-Type', 'text/html; charset=utf-8')]
        start_response(status, headers)
        
        html = f"""
        <html>
            <head><title>Deployment Initialization Error</title></head>
            <body style="font-family: sans-serif; padding: 20px; background: #111; color: #eee;">
                <h2 style="color: #ff6b6b;">Deployment Initialization Error</h2>
                <p>The application failed to initialize during start-up. Here is the traceback:</p>
                <pre style="background: #222; padding: 15px; border-radius: 6px; border: 1px solid #333; overflow-x: auto; color: #ff8b8b;">{self.tb_str}</pre>
            </body>
        </html>
        """
        return [html.encode('utf-8')]

try:
    import os
    from flask import Flask, send_from_directory, make_response
    from flask_cors import CORS
    from database import get_db
    import config

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
    app.config['SECRET_KEY'] = config.SECRET_KEY
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    CORS(app)


    @app.after_request
    def add_security_and_no_cache(response):
        """Prevent browser from caching and add strong security headers."""
        # Disable caching
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        response.headers['Surrogate-Control'] = 'no-store'
        if 'ETag' in response.headers:
            del response.headers['ETag']
        if 'Last-Modified' in response.headers:
            del response.headers['Last-Modified']
            
        # Security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        # Add CSP to permit localhost, Fonts, Chart.js, Three.js, and Firebase APIs
        response.headers['Content-Security-Policy'] = (
            "default-src 'self' blob: https://fonts.googleapis.com https://fonts.gstatic.com https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            "img-src 'self' data:; "
            "connect-src 'self' blob: https://firestore.googleapis.com https://cdn.jsdelivr.net https://cdnjs.cloudflare.com;"
        )
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
        response = make_response(send_from_directory(app.static_folder, 'index.html'))
        return response


    @app.errorhandler(404)
    def not_found(e):
        return {'error': 'Resource not found'}, 404


    @app.errorhandler(500)
    def server_error(e):
        return {'error': 'Internal server error'}, 500

except Exception as import_err:
    app = FallbackApp(traceback.format_exc())


if __name__ == '__main__':
    if not isinstance(app, FallbackApp):
        print("[+] BillFlow Pro is running at http://localhost:5000")
        app.run(host='0.0.0.0', port=5000, debug=True)
    else:
        print("[-] Server failed to import. Traceback:")
        print(app.tb_str)
