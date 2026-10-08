"""
Flask application factory and initialization
"""
from flask import Flask, render_template
from flask_login import LoginManager, current_user
from config import config_dict
from models import db, User, UserProfile
from auth import auth_bp
from products_routes import products_bp


def format_intcomma(value):
    if value is None:
        return '0'
    if isinstance(value, (int, float, Decimal)):
        return format(value, ',')
    return str(value)


def format_date(value, format_string):
    if value is None:
        return ''
    if isinstance(value, (date, datetime)):
        django_to_strftime = {
            'Y': '%Y',
            'y': '%y',
            'm': '%m',
            'd': '%d',
            'M': '%b',
            'F': '%B',
            'H': '%H',
            'i': '%M',
            's': '%S',
        }
        python_format = re.sub(
            r'[YymdMFHis]',
            lambda match: django_to_strftime[match.group()],
            format_string
        )
        return value.strftime(python_format)
    return value


def format_timesince(value):
    if value is None:
        return ''
    now = datetime.now(value.tzinfo) if value.tzinfo else datetime.utcnow()
    seconds = max(int((now - value).total_seconds()), 0)
    intervals = (
        ('year', 31536000),
        ('month', 2592000),
        ('week', 604800),
        ('day', 86400),
        ('hour', 3600),
        ('minute', 60),
        ('second', 1),
    )
    for unit, interval in intervals:
        count = seconds // interval
        if count:
            return f'{count} {unit}{"s" if count != 1 else ""}'
    return '0 seconds'


def truncate_words(value, length=10):
    words = str(value).split()
    if len(words) <= length:
        return ' '.join(words)
    return ' '.join(words[:length]) + '...'


def add_values(value, other):
    return value + other
import os
import re
from datetime import date, datetime
from decimal import Decimal


def create_app(config_name='development'):
    """Application factory function"""
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.jinja_env.filters['intcomma'] = format_intcomma
    app.jinja_env.filters['date'] = format_date
    app.jinja_env.filters['timesince'] = format_timesince
    app.jinja_env.filters['truncatewords'] = truncate_words
    app.jinja_env.filters['add'] = add_values
    
    # Load configuration
    app.config.from_object(config_dict.get(config_name, 'development'))
    
    # Initialize extensions
    db.init_app(app)
    
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(products_bp)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(403)
    def forbidden(error):
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(500)
    def server_error(error):
        return render_template('errors/500.html'), 500
    
    # Context processors
    @app.context_processor
    def inject_user():
        return {'user': current_user}
    
    # CLI commands
    @app.cli.command()
    def init_db():
        """Initialize the database."""
        db.create_all()
        print('Database initialized.')
    
    @app.cli.command()
    def create_admin():
        """Create an admin user."""
        username = input('Username: ')
        email = input('Email: ')
        password = input('Password: ')
        
        if User.query.filter_by(username=username).first():
            print('User already exists.')
            return
        
        user = User(username=username, email=email, first_name='Admin')
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        profile = UserProfile(user_id=user.id, role='admin')
        db.session.add(profile)
        db.session.commit()
        
        print(f'Admin user {username} created successfully.')
    
    return app


if __name__ == '__main__':
    app = create_app(os.getenv('FLASK_ENV', 'development'))
    app.run(debug=True)
