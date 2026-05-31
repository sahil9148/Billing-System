"""
BillFlow Pro — Database Module
SQLite and PostgreSQL database initialization, schema creation, and demo data seeding.
"""
import sqlite3
import os
import bcrypt
from datetime import datetime, timedelta
from config import DATABASE_PATH

# PostgreSQL Support for production cloud hosting (Vercel/Render/Railway)
DATABASE_URL = os.environ.get('DATABASE_URL') or os.environ.get('POSTGRES_URL')

if DATABASE_URL:
    import psycopg2
    import psycopg2.extras

    class PgCursorWrapper:
        def __init__(self, pg_conn, cursor):
            self._conn = pg_conn
            self._cursor = cursor
            self.lastrowid = None

        def execute(self, query, params=None):
            # Translate placeholder '?' to '%s'
            query = query.replace('?', '%s')
            
            # Translate SQLite-specific table creation elements to PostgreSQL syntax
            if "AUTOINCREMENT" in query:
                query = query.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
                # Clean check constraints if any formatting differences exist (standard works on both)
                query = query.replace("CHECK(status IN ('draft','sent','paid','partial','overdue','cancelled'))", "")
                query = query.replace("CHECK(discount_type IN ('percentage','fixed'))", "")

            # Ignore SQLite specific configuration calls
            if query.strip().upper().startswith("PRAGMA "):
                return self

            # Automatically capture inserted IDs by appending RETURNING id to INSERT statements
            is_insert = query.strip().upper().startswith("INSERT INTO ")
            if is_insert:
                query = query.rstrip().rstrip(';') + " RETURNING id"

            # Execute translated query
            self._cursor.execute(query, params)

            # Set self.lastrowid to mimic SQLite behavior
            if is_insert:
                try:
                    row = self._cursor.fetchone()
                    if row:
                        self.lastrowid = row[0]
                except Exception:
                    pass
            
            return self

        def executescript(self, script):
            # PostgreSQL can execute multiple statements separated by semicolons natively
            script = script.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
            self._cursor.execute(script)
            return self

        def fetchone(self):
            return self._cursor.fetchone()

        def fetchall(self):
            return self._cursor.fetchall()

        def close(self):
            self._cursor.close()

        def __iter__(self):
            return iter(self._cursor)

    class PgConnectionWrapper:
        def __init__(self, dsn):
            # Normalize database URI if it starts with older postgres:// scheme
            if dsn.startswith("postgres://"):
                dsn = dsn.replace("postgres://", "postgresql://", 1)
            self._conn = psycopg2.connect(dsn)
            self._cursor_factory = psycopg2.extras.DictCursor
        
        def cursor(self):
            cursor = self._conn.cursor(cursor_factory=self._cursor_factory)
            return PgCursorWrapper(self, cursor)

        def execute(self, query, params=None):
            cursor = self.cursor()
            cursor.execute(query, params)
            return cursor

        def commit(self):
            self._conn.commit()

        def rollback(self):
            self._conn.rollback()

        def close(self):
            self._conn.close()


_DB_INITIALIZED = False

def get_db():
    """Get database connection (or PostgreSQL wrapper) and initialize database lazily."""
    global _DB_INITIALIZED
    
    conn = None
    if DATABASE_URL:
        conn = PgConnectionWrapper(DATABASE_URL)
    else:
        try:
            os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
        except Exception:
            pass
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        
    if not _DB_INITIALIZED:
        _DB_INITIALIZED = True
        try:
            try:
                from config import UPLOAD_FOLDER
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            except Exception:
                pass
            
            cursor = conn.cursor()
            schema_sql = """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    full_name TEXT DEFAULT '',
                    role TEXT DEFAULT 'admin',
                    company_name TEXT DEFAULT '',
                    company_address TEXT DEFAULT '',
                    company_phone TEXT DEFAULT '',
                    company_email TEXT DEFAULT '',
                    company_gstin TEXT DEFAULT '',
                    company_logo TEXT DEFAULT '',
                    default_currency TEXT DEFAULT 'INR',
                    default_tax_rate REAL DEFAULT 18.0,
                    invoice_prefix TEXT DEFAULT 'INV',
                    next_invoice_number INTEGER DEFAULT 1001,
                    payment_terms TEXT DEFAULT 'Net 30',
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS clients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    email TEXT DEFAULT '',
                    phone TEXT DEFAULT '',
                    company TEXT DEFAULT '',
                    billing_address TEXT DEFAULT '',
                    city TEXT DEFAULT '',
                    state TEXT DEFAULT '',
                    zip_code TEXT DEFAULT '',
                    country TEXT DEFAULT 'India',
                    gstin TEXT DEFAULT '',
                    notes TEXT DEFAULT '',
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                );

                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    unit_price REAL NOT NULL DEFAULT 0,
                    tax_rate REAL DEFAULT 18.0,
                    category TEXT DEFAULT 'General',
                    sku TEXT DEFAULT '',
                    unit TEXT DEFAULT 'unit',
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                );

                CREATE TABLE IF NOT EXISTS invoices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    client_id INTEGER NOT NULL,
                    invoice_number TEXT UNIQUE NOT NULL,
                    invoice_date TEXT NOT NULL,
                    due_date TEXT NOT NULL,
                    status TEXT DEFAULT 'draft',
                    subtotal REAL DEFAULT 0,
                    tax_amount REAL DEFAULT 0,
                    discount REAL DEFAULT 0,
                    discount_type TEXT DEFAULT 'percentage',
                    total_amount REAL DEFAULT 0,
                    amount_paid REAL DEFAULT 0,
                    currency TEXT DEFAULT 'INR',
                    notes TEXT DEFAULT '',
                    terms TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (client_id) REFERENCES clients(id)
                );

                CREATE TABLE IF NOT EXISTS invoice_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    invoice_id INTEGER NOT NULL,
                    product_id INTEGER,
                    description TEXT NOT NULL,
                    quantity REAL NOT NULL DEFAULT 1,
                    unit_price REAL NOT NULL DEFAULT 0,
                    tax_rate REAL DEFAULT 0,
                    tax_amount REAL DEFAULT 0,
                    line_total REAL NOT NULL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE,
                    FOREIGN KEY (product_id) REFERENCES products(id)
                );

                CREATE TABLE IF NOT EXISTS payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    invoice_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    payment_date TEXT NOT NULL,
                    amount REAL NOT NULL,
                    payment_method TEXT DEFAULT 'Cash',
                    reference_number TEXT DEFAULT '',
                    notes TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (invoice_id) REFERENCES invoices(id),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                );

                CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    category TEXT NOT NULL DEFAULT 'Miscellaneous',
                    description TEXT DEFAULT '',
                    amount REAL NOT NULL DEFAULT 0,
                    expense_date TEXT NOT NULL,
                    vendor TEXT DEFAULT '',
                    payment_method TEXT DEFAULT 'Cash',
                    is_billable INTEGER DEFAULT 0,
                    client_id INTEGER,
                    notes TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (client_id) REFERENCES clients(id)
                );

                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    message TEXT NOT NULL,
                    response TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                );

                CREATE INDEX IF NOT EXISTS idx_clients_user ON clients(user_id);
                CREATE INDEX IF NOT EXISTS idx_products_user ON products(user_id);
                CREATE INDEX IF NOT EXISTS idx_invoices_user ON invoices(user_id);
                CREATE INDEX IF NOT EXISTS idx_invoices_client ON invoices(client_id);
                CREATE INDEX IF NOT EXISTS idx_invoices_status ON invoices(status);
                CREATE INDEX IF NOT EXISTS idx_invoice_items_invoice ON invoice_items(invoice_id);
                CREATE INDEX IF NOT EXISTS idx_payments_invoice ON payments(invoice_id);
                CREATE INDEX IF NOT EXISTS idx_expenses_user ON expenses(user_id);
            """
            
            if DATABASE_URL:
                cursor.executescript(schema_sql)
            else:
                conn.executescript(schema_sql)
            conn.commit()
            
            cursor.execute("SELECT COUNT(*) FROM users")
            if cursor.fetchone()[0] == 0:
                print("[*] Seeding demo data...")
                seed_demo_data_conn(conn, cursor)
                conn.commit()
                
        except Exception as e:
            print(f"[-] Lazy database initialization failed: {e}")
            _DB_INITIALIZED = False
            
    return conn


def close_db(conn):
    """Close database connection."""
    if conn:
        conn.close()


def init_db():
    """Create all database tables (legacy wrapper)."""
    get_db()
    return True


def seed_demo_data():
    """Seed demo data (legacy wrapper)."""
    get_db()
    return True


def seed_demo_data_conn(conn, cursor):
    """Insert demo data for showcasing the system using the provided connection and cursor."""

    now = datetime.now()
    today = now.strftime('%Y-%m-%d')

    # --- Demo User ---
    pw_hash = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    cursor.execute("""
        INSERT INTO users (username, email, password_hash, full_name, role,
            company_name, company_address, company_phone, company_email,
            company_gstin, default_currency, default_tax_rate, invoice_prefix,
            next_invoice_number, payment_terms)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, ('admin', 'admin@techflow.com', pw_hash, 'Sahil Arora', 'admin',
          'TechFlow Solutions Pvt. Ltd.',
          '42, Electronic City Phase 1, Bengaluru, Karnataka - 560100',
          '+91 98765 43210', 'billing@techflow.com',
          '29AABCT1234F1ZP', 'INR', 18.0, 'INV', 1006, 'Net 30'))
    user_id = cursor.lastrowid

    # --- Demo Clients ---
    clients_data = [
        (user_id, 'Rajesh Sharma', 'rajesh@innovatech.in', '+91 99887 76655',
         'InnovaTech India', '12 MG Road, Pune', 'Pune', 'Maharashtra', '411001', 'India',
         '27AABCI4567G1ZH', 'Key enterprise client'),
        (user_id, 'Priya Patel', 'priya@designhub.co', '+91 88776 65544',
         'DesignHub Creative', '5th Cross, Indiranagar, Bengaluru', 'Bengaluru', 'Karnataka', '560038', 'India',
         '29AABCD7890H1ZK', 'Design and branding projects'),
        (user_id, 'Amit Verma', 'amit@cloudnine.io', '+91 77665 54433',
         'CloudNine Technologies', 'Sector 62, Noida', 'Noida', 'Uttar Pradesh', '201301', 'India',
         '09AABCC2345I1ZM', 'Cloud infrastructure client'),
        (user_id, 'Sarah Johnson', 'sarah@globaledge.com', '+1 415-555-0192',
         'GlobalEdge Inc.', '200 Market Street, San Francisco', 'San Francisco', 'California', '94105', 'USA',
         '', 'International client - USD billing'),
        (user_id, 'Neha Gupta', 'neha@freshmart.in', '+91 66554 43322',
         'FreshMart Retail', 'Anna Salai, Chennai', 'Chennai', 'Tamil Nadu', '600002', 'India',
         '33AABCF5678J1ZP', 'Retail management system'),
    ]
    client_ids = []
    for c in clients_data:
        cursor.execute("""
            INSERT INTO clients (user_id, name, email, phone, company, billing_address,
                city, state, zip_code, country, gstin, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, c)
        client_ids.append(cursor.lastrowid)

    # --- Demo Products ---
    products_data = [
        (user_id, 'Web Development', 'Full-stack web application development', 75000, 18.0, 'Development', 'SRV-001', 'project'),
        (user_id, 'Mobile App Development', 'Native/cross-platform mobile app', 120000, 18.0, 'Development', 'SRV-002', 'project'),
        (user_id, 'UI/UX Design', 'User interface and experience design', 35000, 18.0, 'Design', 'SRV-003', 'project'),
        (user_id, 'Cloud Hosting (Monthly)', 'AWS/GCP managed cloud hosting', 15000, 18.0, 'Infrastructure', 'SRV-004', 'month'),
        (user_id, 'SEO Optimization', 'Search engine optimization package', 25000, 18.0, 'Marketing', 'SRV-005', 'month'),
        (user_id, 'Technical Consultation', 'Expert tech consulting per hour', 5000, 18.0, 'Consulting', 'SRV-006', 'hour'),
        (user_id, 'Database Management', 'Database design, optimization & maintenance', 20000, 18.0, 'Infrastructure', 'SRV-007', 'month'),
        (user_id, 'API Integration', 'Third-party API integration service', 40000, 18.0, 'Development', 'SRV-008', 'project'),
    ]
    product_ids = []
    for p in products_data:
        cursor.execute("""
            INSERT INTO products (user_id, name, description, unit_price, tax_rate,
                category, sku, unit)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, p)
        product_ids.append(cursor.lastrowid)

    # --- Demo Invoices with Items ---
    def make_invoice(inv_num, client_idx, date_offset, due_offset, status, items, discount=0, disc_type='percentage'):
        inv_date = (now - timedelta(days=date_offset)).strftime('%Y-%m-%d')
        due_date = (now - timedelta(days=due_offset)).strftime('%Y-%m-%d')

        subtotal = sum(qty * price for _, _, qty, price, _ in items)
        tax_total = sum(qty * price * rate / 100 for _, _, qty, price, rate in items)
        if disc_type == 'percentage':
            disc_val = subtotal * discount / 100
        else:
            disc_val = discount
        total = subtotal - disc_val + tax_total

        amount_paid = total if status == 'paid' else (total * 0.4 if status == 'partial' else 0)

        cursor.execute("""
            INSERT INTO invoices (user_id, client_id, invoice_number, invoice_date,
                due_date, status, subtotal, tax_amount, discount, discount_type,
                total_amount, amount_paid, currency, notes, terms)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, client_ids[client_idx], inv_num, inv_date, due_date, status,
              round(subtotal, 2), round(tax_total, 2), discount, disc_type,
              round(total, 2), round(amount_paid, 2), 'INR',
              'Thank you for your business!', 'Payment due within 30 days of invoice date.'))
        inv_id = cursor.lastrowid

        for prod_idx, desc, qty, price, rate in items:
            tax_amt = round(qty * price * rate / 100, 2)
            line = round(qty * price + tax_amt, 2)
            cursor.execute("""
                INSERT INTO invoice_items (invoice_id, product_id, description,
                    quantity, unit_price, tax_rate, tax_amount, line_total)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (inv_id, product_ids[prod_idx] if prod_idx is not None else None,
                  desc, qty, price, rate, tax_amt, line))

        return inv_id, amount_paid

    inv1_id, inv1_paid = make_invoice('INV-1001', 0, 45, 15, 'paid', [
        (0, 'E-commerce Website Development', 1, 75000, 18),
        (2, 'UI/UX Design for E-commerce', 1, 35000, 18),
        (5, 'Technical Consultation (10 hrs)', 10, 5000, 18),
    ], discount=5)

    inv2_id, inv2_paid = make_invoice('INV-1002', 1, 30, 0, 'sent', [
        (2, 'Brand Identity Design Package', 1, 35000, 18),
        (4, 'SEO Optimization - 3 months', 3, 25000, 18),
    ])

    inv3_id, inv3_paid = make_invoice('INV-1003', 2, 60, 30, 'partial', [
        (1, 'Inventory Management Mobile App', 1, 120000, 18),
        (3, 'Cloud Hosting Setup & 3 Months', 3, 15000, 18),
        (6, 'Database Design & Optimization', 1, 20000, 18),
    ], discount=10)

    inv4_id, inv4_paid = make_invoice('INV-1004', 3, 90, 60, 'overdue', [
        (7, 'Payment Gateway API Integration', 1, 40000, 18),
        (5, 'Technical Consultation (5 hrs)', 5, 5000, 18),
    ])

    inv5_id, _ = make_invoice('INV-1005', 4, 5, -25, 'draft', [
        (0, 'Retail POS Web Application', 1, 75000, 18),
        (1, 'Mobile App for Inventory', 1, 120000, 18),
        (6, 'Database Management - 6 months', 6, 20000, 18),
    ], discount=8)

    # --- Demo Payments ---
    if inv1_paid > 0:
        cursor.execute("""
            INSERT INTO payments (invoice_id, user_id, payment_date, amount,
                payment_method, reference_number, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (inv1_id, user_id, (now - timedelta(days=20)).strftime('%Y-%m-%d'),
              inv1_paid, 'Bank Transfer', 'NEFT-2026-04-001', 'Full payment received'))

    if inv3_paid > 0:
        cursor.execute("""
            INSERT INTO payments (invoice_id, user_id, payment_date, amount,
                payment_method, reference_number, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (inv3_id, user_id, (now - timedelta(days=15)).strftime('%Y-%m-%d'),
              inv3_paid, 'UPI', 'UPI-2026-05-003', 'Partial payment - 40%'))

    cursor.execute("""
        INSERT INTO payments (invoice_id, user_id, payment_date, amount,
            payment_method, reference_number, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (inv1_id, user_id, (now - timedelta(days=40)).strftime('%Y-%m-%d'),
          25000, 'Credit Card', 'CC-2026-03-001', 'Advance payment'))

    # --- Demo Expenses ---
    expenses_data = [
        (user_id, 'Software', 'AWS Cloud Services - Monthly', 45000,
         (now - timedelta(days=10)).strftime('%Y-%m-%d'), 'Amazon Web Services', 'Credit Card', ''),
        (user_id, 'Office Supplies', 'Office furniture and equipment', 32000,
         (now - timedelta(days=20)).strftime('%Y-%m-%d'), 'Urban Ladder', 'Bank Transfer', ''),
        (user_id, 'Marketing', 'Google Ads Campaign - May', 28000,
         (now - timedelta(days=5)).strftime('%Y-%m-%d'), 'Google', 'Credit Card', ''),
        (user_id, 'Utilities', 'Internet and Phone Bills', 5500,
         (now - timedelta(days=3)).strftime('%Y-%m-%d'), 'Airtel', 'UPI', ''),
        (user_id, 'Travel', 'Client meeting - Mumbai trip', 18000,
         (now - timedelta(days=15)).strftime('%Y-%m-%d'), 'MakeMyTrip', 'Credit Card', ''),
        (user_id, 'Salaries', 'Freelancer payment - Design', 50000,
         (now - timedelta(days=8)).strftime('%Y-%m-%d'), 'Freelancer', 'Bank Transfer', ''),
    ]
    for e in expenses_data:
        cursor.execute("""
            INSERT INTO expenses (user_id, category, description, amount,
                expense_date, vendor, payment_method, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, e)

    conn.commit()
    close_db(conn)
    print("[+] Demo data seeded successfully!")
