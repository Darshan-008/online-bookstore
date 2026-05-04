from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import User, Book

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    """Decorator to ensure the current user is admin."""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            if request.is_json:
                return jsonify({'error': 'Admin access required.'}), 403
            flash('Admin access required.', 'danger')
            return redirect(url_for('auth.login_page'))
        return f(*args, **kwargs)
    return decorated


# ─── Pages ───────────────────────────────────────────────
@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    return render_template('admin/dashboard.html')


@admin_bp.route('/books')
@login_required
@admin_required
def manage_books_page():
    books = Book.query.order_by(Book.created_at.desc()).all()
    return render_template('admin/manage_books.html', books=books)


@admin_bp.route('/users')
@login_required
@admin_required
def manage_users_page():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/manage_users.html', users=users)


# ─── Book CRUD API ───────────────────────────────────────
@admin_bp.route('/api/books', methods=['POST'])
@login_required
@admin_required
def add_book():
    data = request.get_json() if request.is_json else request.form
    title = data.get('title', '').strip()
    author = data.get('author', '').strip()
    price = data.get('price')
    description = data.get('description', '').strip()
    image_url = data.get('image_url', '').strip()

    if not title or not author or not price:
        msg = 'Title, author, and price are required.'
        if request.is_json:
            return jsonify({'error': msg}), 400
        flash(msg, 'danger')
        return redirect(url_for('admin.manage_books_page'))

    book = Book(title=title, author=author, price=float(price),
                description=description, image_url=image_url)
    db.session.add(book)
    db.session.commit()

    if request.is_json:
        return jsonify({'message': 'Book added.', 'book': book.to_dict()}), 201

    flash(f'Book "{title}" added!', 'success')
    return redirect(url_for('admin.manage_books_page'))


@admin_bp.route('/api/books/<int:book_id>', methods=['PUT', 'POST'])
@login_required
@admin_required
def edit_book(book_id):
    book = Book.query.get_or_404(book_id)
    data = request.get_json() if request.is_json else request.form

    book.title = data.get('title', book.title).strip()
    book.author = data.get('author', book.author).strip()
    book.price = float(data.get('price', book.price))
    book.description = data.get('description', book.description).strip()
    book.image_url = data.get('image_url', book.image_url).strip()
    db.session.commit()

    if request.is_json:
        return jsonify({'message': 'Book updated.', 'book': book.to_dict()})

    flash(f'Book "{book.title}" updated!', 'success')
    return redirect(url_for('admin.manage_books_page'))


@admin_bp.route('/api/books/<int:book_id>/delete', methods=['DELETE', 'POST'])
@login_required
@admin_required
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)
    title = book.title
    db.session.delete(book)
    db.session.commit()

    if request.is_json:
        return jsonify({'message': f'Book "{title}" deleted.'})

    flash(f'Book "{title}" deleted.', 'info')
    return redirect(url_for('admin.manage_books_page'))


# ─── User Management ────────────────────────────────────
@admin_bp.route('/api/users/<int:user_id>/delete', methods=['DELETE', 'POST'])
@login_required
@admin_required
def delete_user(user_id):
    if user_id == current_user.id:
        msg = 'Cannot delete yourself.'
        if request.is_json:
            return jsonify({'error': msg}), 400
        flash(msg, 'danger')
        return redirect(url_for('admin.manage_users_page'))

    user = User.query.get_or_404(user_id)
    name = user.name
    db.session.delete(user)
    db.session.commit()

    if request.is_json:
        return jsonify({'message': f'User "{name}" deleted.'})

    flash(f'User "{name}" deleted.', 'info')
    return redirect(url_for('admin.manage_users_page'))


@admin_bp.route('/api/users/<int:user_id>/toggle-admin', methods=['POST'])
@login_required
@admin_required
def toggle_admin(user_id):
    if user_id == current_user.id:
        msg = 'Cannot modify your own admin status.'
        if request.is_json:
            return jsonify({'error': msg}), 400
        flash(msg, 'danger')
        return redirect(url_for('admin.manage_users_page'))

    user = User.query.get_or_404(user_id)
    user.is_admin = not user.is_admin
    db.session.commit()

    if request.is_json:
        return jsonify({'message': f'User "{user.name}" admin status: {user.is_admin}'})

    flash(f'User "{user.name}" admin status toggled.', 'success')
    return redirect(url_for('admin.manage_users_page'))
