#!/usr/bin/env python
"""
Run the Flask application
"""
import os
from app import create_app, db
from models import User, UserProfile, Category, Product, StockMovement

app = create_app(os.getenv('FLASK_ENV', 'development'))

@app.shell_context_processor
def make_shell_context():
    """Register models with shell context"""
    return {
        'db': db,
        'User': User,
        'UserProfile': UserProfile,
        'Category': Category,
        'Product': Product,
        'StockMovement': StockMovement,
    }

if __name__ == '__main__':
    app.run(
        host=os.getenv('FLASK_HOST', '127.0.0.1'),
        port=int(os.getenv('FLASK_PORT', 5000)),
        debug=os.getenv('FLASK_DEBUG', True)
    )
