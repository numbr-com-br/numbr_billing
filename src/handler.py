"""
AWS Lambda handler for Flask application
"""
from src.main import app

# Zappa will use the Flask app directly
handler = app