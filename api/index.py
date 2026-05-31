import os
import sys

# Ensure the parent directory (project root) is added to PYTHONPATH
# so that Vercel's serverless environment can successfully import app.py and local packages.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
