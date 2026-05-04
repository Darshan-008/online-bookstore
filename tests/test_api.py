"""
API Tests for BookHaven Online Book Store
Run: python -m pytest tests/test_api.py -v
"""
import os
import sys
import json
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app, db
from app.models import User, Book
import bcrypt


@pytest.fixture
def app():
    """Create a test app with an in-memory database."""
    app = create_app()
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False

    with app.app_context():
        db.create_all()
        # Seed a test book
        book = Book(title='Test Book', author='Test Author', price=199.99,
                    description='A test book')
        db.session.add(book)
        db.session.commit()

    yield app

    with app.app_context():
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def register_user(client, name='Test User', email='test@test.com', password='test123'):
    return client.post('/api/auth/register', json={
        'name': name, 'email': email, 'password': password
    })


def login_user(client, email='test@test.com', password='test123'):
    return client.post('/api/auth/login', json={
        'email': email, 'password': password
    })


# ── Auth Tests ───────────────────────────────────────────
class TestAuth:
    def test_register_success(self, client):
        res = register_user(client)
        assert res.status_code == 201
        data = res.get_json()
        assert data['user']['email'] == 'test@test.com'

    def test_register_duplicate_email(self, client):
        register_user(client)
        res = register_user(client)
        assert res.status_code == 409

    def test_register_missing_fields(self, client):
        res = client.post('/api/auth/register', json={'name': 'Test'})
        assert res.status_code == 400

    def test_register_short_password(self, client):
        res = client.post('/api/auth/register', json={
            'name': 'Test', 'email': 'x@x.com', 'password': '123'
        })
        assert res.status_code == 400

    def test_login_success(self, client):
        register_user(client)
        client.get('/api/auth/logout')
        res = login_user(client)
        assert res.status_code == 200

    def test_login_wrong_password(self, client):
        register_user(client)
        client.get('/api/auth/logout')
        res = login_user(client, password='wrong')
        assert res.status_code == 401

    def test_logout(self, client):
        register_user(client)
        res = client.post('/api/auth/logout')
        assert res.status_code in (200, 302)


# ── Books Tests ──────────────────────────────────────────
class TestBooks:
    def test_get_books(self, client):
        res = client.get('/api/books')
        assert res.status_code == 200
        data = res.get_json()
        assert len(data) >= 1

    def test_get_single_book(self, client, app):
        with app.app_context():
            book = Book.query.first()
        res = client.get(f'/api/books/{book.id}')
        assert res.status_code == 200
        assert res.get_json()['title'] == 'Test Book'

    def test_search_books(self, client):
        res = client.get('/api/books?search=Test')
        data = res.get_json()
        assert any('Test' in b['title'] for b in data)


# ── Cart Tests ───────────────────────────────────────────
class TestCart:
    def test_add_to_cart(self, client, app):
        register_user(client)
        with app.app_context():
            book = Book.query.first()
        res = client.post('/api/cart/add', json={'book_id': book.id})
        assert res.status_code == 200

    def test_view_cart(self, client, app):
        register_user(client)
        with app.app_context():
            book = Book.query.first()
        client.post('/api/cart/add', json={'book_id': book.id})
        res = client.get('/api/cart')
        assert res.status_code == 200
        data = res.get_json()
        assert len(data['items']) == 1

    def test_remove_from_cart(self, client, app):
        register_user(client)
        with app.app_context():
            book = Book.query.first()
        client.post('/api/cart/add', json={'book_id': book.id})
        cart = client.get('/api/cart').get_json()
        item_id = cart['items'][0]['id']
        res = client.delete(f'/api/cart/remove/{item_id}')
        assert res.status_code in (200, 302)

    def test_cart_requires_login(self, client):
        res = client.get('/api/cart')
        assert res.status_code in (302, 401, 403)


# ── Checkout / Payment Tests ────────────────────────────
class TestPayment:
    def test_checkout_success(self, client, app):
        register_user(client)
        with app.app_context():
            book = Book.query.first()
        client.post('/api/cart/add', json={'book_id': book.id})
        res = client.post('/api/checkout', json={
            'payment_method': 'card',
            'shipping_address': '123 Main St',
            'shipping_city': 'New York',
            'shipping_zip': '10001',
            'card_name': 'Test User',
            'card_number': '1111222233334444',
            'card_expiry': '12/26',
            'card_cvv': '123'
        })
        assert res.status_code == 201
        data = res.get_json()
        assert data['order']['payment_status'] == 'completed'

    def test_checkout_empty_cart(self, client):
        register_user(client)
        res = client.post('/api/checkout', json={
            'payment_method': 'card',
            'shipping_address': '123 Main St',
            'shipping_city': 'New York',
            'shipping_zip': '10001',
            'card_name': 'Test User',
            'card_number': '1111222233334444',
            'card_expiry': '12/26',
            'card_cvv': '123'
        })
        assert res.status_code == 400

    def test_view_orders(self, client, app):
        register_user(client)
        with app.app_context():
            book = Book.query.first()
        client.post('/api/cart/add', json={'book_id': book.id})
        client.post('/api/checkout', json={
            'payment_method': 'upi',
            'shipping_address': '123 Main St',
            'shipping_city': 'New York',
            'shipping_zip': '10001'
        })
        res = client.get('/api/orders')
        assert res.status_code == 200
        assert len(res.get_json()) == 1


# ── Analytics Tests ──────────────────────────────────────
class TestAnalytics:
    def test_user_analytics(self, client, app):
        register_user(client)
        with app.app_context():
            book = Book.query.first()
        client.post('/api/cart/add', json={'book_id': book.id})
        client.post('/api/checkout', json={
            'payment_method': 'card',
            'shipping_address': '123 Main St',
            'shipping_city': 'New York',
            'shipping_zip': '10001',
            'card_name': 'Test User',
            'card_number': '1111222233334444',
            'card_expiry': '12/26',
            'card_cvv': '123'
        })
        res = client.get('/api/analytics/user')
        assert res.status_code == 200
        data = res.get_json()
        assert data['total_orders'] >= 1

    def test_admin_analytics_forbidden(self, client):
        register_user(client)
        res = client.get('/api/analytics/admin')
        assert res.status_code == 403
