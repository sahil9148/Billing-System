"""
BillFlow Pro — Configuration Settings
"""
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Security
SECRET_KEY = os.environ.get('SECRET_KEY', 'billflow-pro-secret-key-change-in-production-2026')
JWT_EXPIRATION_HOURS = 24

# Database
# Check if running on Vercel or other serverless environment with a read-only filesystem
if os.environ.get('VERCEL') == '1':
    DATABASE_PATH = '/tmp/billing.db'
    UPLOAD_FOLDER = '/tmp/uploads'
else:
    DATABASE_PATH = os.path.join(BASE_DIR, 'data', 'billing.db')
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')

# Supported Currencies
CURRENCIES = {
    'INR': {'symbol': '₹', 'name': 'Indian Rupee'},
    'USD': {'symbol': '$', 'name': 'US Dollar'},
    'EUR': {'symbol': '€', 'name': 'Euro'},
    'GBP': {'symbol': '£', 'name': 'British Pound'},
    'AUD': {'symbol': 'A$', 'name': 'Australian Dollar'},
    'CAD': {'symbol': 'C$', 'name': 'Canadian Dollar'},
    'JPY': {'symbol': '¥', 'name': 'Japanese Yen'},
}

# GST Rates (India)
GST_RATES = {
    0: 'Exempt (0%)',
    5: 'GST 5%',
    12: 'GST 12%',
    18: 'GST 18%',
    28: 'GST 28%',
}

DEFAULT_TAX_RATE = 18.0

# Invoice Statuses
INVOICE_STATUSES = ['draft', 'sent', 'paid', 'partial', 'overdue', 'cancelled']

# Payment Methods
PAYMENT_METHODS = [
    'Cash', 'Bank Transfer', 'UPI', 'Credit Card',
    'Debit Card', 'Cheque', 'Online', 'Other'
]

# Expense Categories
EXPENSE_CATEGORIES = [
    'Office Supplies', 'Travel', 'Utilities', 'Rent',
    'Marketing', 'Software', 'Hardware', 'Professional Services',
    'Insurance', 'Salaries', 'Food & Beverages', 'Miscellaneous'
]
