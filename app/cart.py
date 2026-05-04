from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import CartItem, Book

cart_bp = Blueprint('cart', __name__)


# ─── Pages ───────────────────────────────────────────────
@cart_bp.route('/cart')
@login_required
def cart_page():
    items = CartItem.query.filter_by(user_id=current_user.id).all()
    total = sum(item.book.price * item.quantity for item in items)
    return render_template('cart.html', items=items, total=round(total, 2))


# ─── API ─────────────────────────────────────────────────
@cart_bp.route('/api/cart')
@login_required
def get_cart():
    items = CartItem.query.filter_by(user_id=current_user.id).all()
    total = sum(item.book.price * item.quantity for item in items)
    return jsonify({'items': [i.to_dict() for i in items], 'total': round(total, 2)})


@cart_bp.route('/api/cart/add', methods=['POST'])
@login_required
def add_to_cart():
    data = request.get_json() if request.is_json else request.form
    book_id = data.get('book_id')
    quantity = int(data.get('quantity', 1))

    if not book_id:
        if request.is_json:
            return jsonify({'error': 'book_id is required.'}), 400
        flash('Book ID is required.', 'danger')
        return redirect(url_for('books.books_page'))

    book = Book.query.get(book_id)
    if not book:
        if request.is_json:
            return jsonify({'error': 'Book not found.'}), 404
        flash('Book not found.', 'danger')
        return redirect(url_for('books.books_page'))

    existing = CartItem.query.filter_by(user_id=current_user.id, book_id=book_id).first()
    if existing:
        existing.quantity += quantity
    else:
        item = CartItem(user_id=current_user.id, book_id=book_id, quantity=quantity)
        db.session.add(item)

    db.session.commit()

    if request.is_json:
        return jsonify({'message': 'Added to cart.'}), 200

    flash(f'"{book.title}" added to cart!', 'success')
    return redirect(url_for('books.books_page'))


@cart_bp.route('/api/cart/update/<int:item_id>', methods=['PUT', 'POST'])
@login_required
def update_cart(item_id):
    item = CartItem.query.filter_by(id=item_id, user_id=current_user.id).first_or_404()
    data = request.get_json() if request.is_json else request.form
    quantity = int(data.get('quantity', 1))

    if quantity <= 0:
        db.session.delete(item)
    else:
        item.quantity = quantity

    db.session.commit()

    if request.is_json:
        return jsonify({'message': 'Cart updated.'}), 200
    return redirect(url_for('cart.cart_page'))


@cart_bp.route('/api/cart/remove/<int:item_id>', methods=['DELETE', 'POST'])
@login_required
def remove_from_cart(item_id):
    item = CartItem.query.filter_by(id=item_id, user_id=current_user.id).first_or_404()
    db.session.delete(item)
    db.session.commit()

    if request.is_json:
        return jsonify({'message': 'Removed from cart.'}), 200

    flash('Item removed from cart.', 'info')
    return redirect(url_for('cart.cart_page'))
