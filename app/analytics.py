from flask import Blueprint, jsonify, render_template
from flask_login import login_required, current_user
from sqlalchemy import func, extract
from app import db
from app.models import User, Book, Order, OrderItem

analytics_bp = Blueprint('analytics', __name__)


# ─── Pages ───────────────────────────────────────────────
@analytics_bp.route('/analytics')
@login_required
def user_analytics_page():
    return render_template('analytics.html')


@analytics_bp.route('/admin/analytics')
@login_required
def admin_analytics_page():
    if not current_user.is_admin:
        return render_template('analytics.html')
    return render_template('admin/dashboard.html')


# ─── User Analytics API ─────────────────────────────────
@analytics_bp.route('/api/analytics/user')
@login_required
def user_analytics():
    user_id = current_user.id

    # Summary stats
    total_orders = Order.query.filter_by(user_id=user_id, payment_status='completed').count()
    total_spent = db.session.query(
        func.coalesce(func.sum(Order.total_amount), 0)
    ).filter_by(user_id=user_id, payment_status='completed').scalar()

    # Monthly spending (last 12 months)
    monthly = db.session.query(
        extract('year', Order.created_at).label('year'),
        extract('month', Order.created_at).label('month'),
        func.sum(Order.total_amount).label('total')
    ).filter_by(user_id=user_id, payment_status='completed') \
     .group_by('year', 'month') \
     .order_by('year', 'month').all()

    monthly_data = [{'year': int(r.year), 'month': int(r.month), 'total': round(r.total, 2)} for r in monthly]

    # Favorite authors
    fav_authors = db.session.query(
        Book.author,
        func.sum(OrderItem.quantity).label('count')
    ).join(OrderItem, OrderItem.book_id == Book.id) \
     .join(Order, Order.id == OrderItem.order_id) \
     .filter(Order.user_id == user_id, Order.payment_status == 'completed') \
     .group_by(Book.author) \
     .order_by(func.sum(OrderItem.quantity).desc()) \
     .limit(5).all()

    # Recent orders
    recent = Order.query.filter_by(user_id=user_id).order_by(
        Order.created_at.desc()
    ).limit(5).all()

    return jsonify({
        'total_orders': total_orders,
        'total_spent': round(float(total_spent), 2),
        'monthly_spending': monthly_data,
        'favorite_authors': [{'author': a, 'count': int(c)} for a, c in fav_authors],
        'recent_orders': [o.to_dict() for o in recent]
    })


# ─── Admin Analytics API ────────────────────────────────
@analytics_bp.route('/api/analytics/admin')
@login_required
def admin_analytics():
    if not current_user.is_admin:
        return jsonify({'error': 'Admin access required.'}), 403

    total_revenue = db.session.query(
        func.coalesce(func.sum(Order.total_amount), 0)
    ).filter_by(payment_status='completed').scalar()

    total_users = User.query.count()
    total_orders = Order.query.filter_by(payment_status='completed').count()
    total_books = Book.query.count()

    # Revenue by month
    monthly_revenue = db.session.query(
        extract('year', Order.created_at).label('year'),
        extract('month', Order.created_at).label('month'),
        func.sum(Order.total_amount).label('total')
    ).filter_by(payment_status='completed') \
     .group_by('year', 'month') \
     .order_by('year', 'month').all()

    # Top selling books
    top_books = db.session.query(
        Book.title,
        Book.author,
        func.sum(OrderItem.quantity).label('sold')
    ).join(OrderItem, OrderItem.book_id == Book.id) \
     .join(Order, Order.id == OrderItem.order_id) \
     .filter(Order.payment_status == 'completed') \
     .group_by(Book.id) \
     .order_by(func.sum(OrderItem.quantity).desc()) \
     .limit(10).all()

    # New users by month
    new_users = db.session.query(
        extract('year', User.created_at).label('year'),
        extract('month', User.created_at).label('month'),
        func.count(User.id).label('count')
    ).group_by('year', 'month').order_by('year', 'month').all()

    return jsonify({
        'total_revenue': round(float(total_revenue), 2),
        'total_users': total_users,
        'total_orders': total_orders,
        'total_books': total_books,
        'monthly_revenue': [{'year': int(r.year), 'month': int(r.month), 'total': round(r.total, 2)} for r in monthly_revenue],
        'top_books': [{'title': t, 'author': a, 'sold': int(s)} for t, a, s in top_books],
        'new_users': [{'year': int(r.year), 'month': int(r.month), 'count': int(r.count)} for r in new_users]
    })
