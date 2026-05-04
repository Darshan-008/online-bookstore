from datetime import datetime
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from app import db
from app.models import CartItem, Order, OrderItem

payment_bp = Blueprint('payment', __name__)


def generate_invoice_number():
    """Generate a unique invoice number: INV-YYYYMMDD-XXXX"""
    today = datetime.utcnow().strftime('%Y%m%d')
    count = Order.query.filter(Order.invoice_number.like(f'INV-{today}-%')).count()
    return f'INV-{today}-{count + 1:04d}'


# ─── Pages ───────────────────────────────────────────────
@payment_bp.route('/checkout')
@login_required
def checkout_page():
    items = CartItem.query.filter_by(user_id=current_user.id).all()
    if not items:
        flash('Your cart is empty.', 'warning')
        return redirect(url_for('cart.cart_page'))
    total = sum(item.book.price * item.quantity for item in items)
    return render_template('checkout.html', items=items, total=round(total, 2))


@payment_bp.route('/orders')
@login_required
def order_history_page():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('order_history.html', orders=orders)


@payment_bp.route('/orders/<int:order_id>')
@login_required
def order_detail_page(order_id):
    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first_or_404()
    return render_template('order_success.html', order=order)


# ─── API ─────────────────────────────────────────────────
@payment_bp.route('/api/checkout', methods=['POST'])
@login_required
def checkout():
    data = request.get_json() if request.is_json else request.form
    payment_method = data.get('payment_method', 'card').lower()

    if payment_method not in ('card', 'upi', 'cod'):
        msg = 'Invalid payment method. Choose card, upi, or cod.'
        if request.is_json:
            return jsonify({'error': msg}), 400
        flash(msg, 'danger')
        return redirect(url_for('payment.checkout_page'))

    # Extract Shipping Details
    shipping_address = data.get('shipping_address', '').strip()
    shipping_city = data.get('shipping_city', '').strip()
    shipping_zip = data.get('shipping_zip', '').strip()

    if not shipping_address or not shipping_city or not shipping_zip:
        msg = 'Shipping address, city, and ZIP code are required.'
        if request.is_json:
            return jsonify({'error': msg}), 400
        flash(msg, 'danger')
        return redirect(url_for('payment.checkout_page'))

    # Card Details Validation (Simulation only)
    if payment_method == 'card':
        card_name = data.get('card_name', '').strip()
        card_number = data.get('card_number', '').strip()
        card_expiry = data.get('card_expiry', '').strip()
        card_cvv = data.get('card_cvv', '').strip()
        
        if not card_name or not card_number or not card_expiry or not card_cvv:
            msg = 'All card details are required when paying with card.'
            if request.is_json:
                return jsonify({'error': msg}), 400
            flash(msg, 'danger')
            return redirect(url_for('payment.checkout_page'))

    # Get cart items
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    if not cart_items:
        msg = 'Your cart is empty.'
        if request.is_json:
            return jsonify({'error': msg}), 400
        flash(msg, 'warning')
        return redirect(url_for('cart.cart_page'))

    # Calculate total
    total = sum(item.book.price * item.quantity for item in cart_items)

    # Simulate payment (always succeeds in dev)
    payment_status = 'completed'

    # Create order
    order = Order(
        user_id=current_user.id,
        total_amount=round(total, 2),
        payment_method=payment_method,
        payment_status=payment_status,
        order_status='placed',
        invoice_number=generate_invoice_number(),
        shipping_address=shipping_address,
        shipping_city=shipping_city,
        shipping_zip=shipping_zip
    )
    db.session.add(order)
    db.session.flush()  # Get order.id

    # Create order items (snapshot prices)
    for cart_item in cart_items:
        oi = OrderItem(
            order_id=order.id,
            book_id=cart_item.book_id,
            quantity=cart_item.quantity,
            price=cart_item.book.price
        )
        db.session.add(oi)

    # Clear cart
    CartItem.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()

    # Generate PDF invoice
    try:
        from app.invoice import generate_pdf_invoice
        generate_pdf_invoice(order)
    except Exception as e:
        current_app.logger.error(f'Invoice generation failed: {e}')

    if request.is_json:
        return jsonify({
            'message': 'Order placed successfully!',
            'order': order.to_dict()
        }), 201

    flash('Order placed successfully!', 'success')
    return redirect(url_for('payment.order_detail_page', order_id=order.id))


@payment_bp.route('/api/orders')
@login_required
def get_orders():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return jsonify([o.to_dict() for o in orders])


@payment_bp.route('/api/orders/<int:order_id>')
@login_required
def get_order(order_id):
    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first_or_404()
    return jsonify(order.to_dict())
