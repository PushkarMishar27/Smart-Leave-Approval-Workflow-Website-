import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'smartleave_super_secret_key_2026_prod_grade')
    
    # MySQL Database Config (Default parameters)
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT', 3306))
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
    MYSQL_DB = os.environ.get('MYSQL_DB', 'smartleave_db')
    
    # SQLite Fallback DB Path
    SQLITE_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'smartleave.db')
    
    # App Settings
    APP_NAME = "SmartLeave"
    TAGLINE = "Leave management, intelligently simplified."
    DEVELOPMENT_MODE = True
