import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', 'sqlite:///' + os.path.join(basedir, 'instance', 'bookstore.db')
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    INVOICE_FOLDER = os.path.join(basedir, 'app', 'static', 'invoices')
