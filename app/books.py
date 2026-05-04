from flask import Blueprint, request, jsonify, render_template
from app.models import Book

books_bp = Blueprint('books', __name__)


# ─── Pages ───────────────────────────────────────────────
@books_bp.route('/')
@books_bp.route('/books')
def books_page():
    search = request.args.get('search', '').strip()
    if search:
        books = Book.query.filter(
            (Book.title.ilike(f'%{search}%')) | (Book.author.ilike(f'%{search}%'))
        ).all()
    else:
        books = Book.query.order_by(Book.created_at.desc()).all()
    return render_template('books.html', books=books, search=search)


@books_bp.route('/books/<int:book_id>')
def book_detail_page(book_id):
    book = Book.query.get_or_404(book_id)
    return render_template('book_detail.html', book=book)


# ─── API ─────────────────────────────────────────────────
@books_bp.route('/api/books')
def get_books():
    search = request.args.get('search', '').strip()
    if search:
        books = Book.query.filter(
            (Book.title.ilike(f'%{search}%')) | (Book.author.ilike(f'%{search}%'))
        ).all()
    else:
        books = Book.query.order_by(Book.created_at.desc()).all()
    return jsonify([b.to_dict() for b in books])


@books_bp.route('/api/books/<int:book_id>')
def get_book(book_id):
    book = Book.query.get_or_404(book_id)
    return jsonify(book.to_dict())
