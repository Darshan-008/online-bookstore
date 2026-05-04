from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
import bcrypt
from app import db
from app.models import User

auth_bp = Blueprint('auth', __name__)


# ─── Pages ───────────────────────────────────────────────
@auth_bp.route('/login')
def login_page():
    if current_user.is_authenticated:
        return redirect(url_for('books.books_page'))
    return render_template('login.html')


@auth_bp.route('/register')
def register_page():
    if current_user.is_authenticated:
        return redirect(url_for('books.books_page'))
    return render_template('register.html')


# ─── API ─────────────────────────────────────────────────
@auth_bp.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json() if request.is_json else request.form
    name = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not name or not email or not password:
        msg = 'Name, email, and password are required.'
        if request.is_json:
            return jsonify({'error': msg}), 400
        flash(msg, 'danger')
        return redirect(url_for('auth.register_page'))

    if User.query.filter_by(email=email).first():
        msg = 'Email already registered.'
        if request.is_json:
            return jsonify({'error': msg}), 409
        flash(msg, 'danger')
        return redirect(url_for('auth.register_page'))

    if len(password) < 6:
        msg = 'Password must be at least 6 characters.'
        if request.is_json:
            return jsonify({'error': msg}), 400
        flash(msg, 'danger')
        return redirect(url_for('auth.register_page'))

    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    user = User(name=name, email=email, password=hashed)
    db.session.add(user)
    db.session.commit()

    login_user(user)

    if request.is_json:
        return jsonify({'message': 'Registered successfully.', 'user': user.to_dict()}), 201

    flash('Account created successfully!', 'success')
    return redirect(url_for('books.books_page'))


@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json() if request.is_json else request.form
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not email or not password:
        msg = 'Email and password are required.'
        if request.is_json:
            return jsonify({'error': msg}), 400
        flash(msg, 'danger')
        return redirect(url_for('auth.login_page'))

    user = User.query.filter_by(email=email).first()
    if not user or not bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
        msg = 'Invalid email or password.'
        if request.is_json:
            return jsonify({'error': msg}), 401
        flash(msg, 'danger')
        return redirect(url_for('auth.login_page'))

    login_user(user)

    if request.is_json:
        return jsonify({'message': 'Logged in.', 'user': user.to_dict()}), 200

    flash(f'Welcome back, {user.name}!', 'success')
    if user.is_admin:
        return redirect(url_for('admin.dashboard'))
    return redirect(url_for('books.books_page'))


@auth_bp.route('/api/auth/logout', methods=['POST', 'GET'])
@login_required
def logout():
    logout_user()
    if request.is_json:
        return jsonify({'message': 'Logged out.'}), 200
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login_page'))
