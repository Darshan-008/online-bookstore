"""
Seed the database with sample books, users, and orders for development/testing.
Run: python seed.py
"""
import os
import sys
from datetime import datetime, timedelta
import random

# Ensure app is importable
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models import User, Book, CartItem, Order, OrderItem
import bcrypt


def seed():
    app = create_app()
    with app.app_context():
        print('[*] Clearing existing data...')
        OrderItem.query.delete()
        Order.query.delete()
        CartItem.query.delete()
        Book.query.delete()
        User.query.delete()
        db.session.commit()

        # ── Users ────────────────────────────────────────
        print('[+] Creating users...')
        pwd = bcrypt.hashpw('password123'.encode(), bcrypt.gensalt()).decode()

        admin = User(name='Admin User', email='admin@bookhaven.com', password=pwd,
                     is_admin=True, created_at=datetime.utcnow() - timedelta(days=90))
        user1 = User(name='Ravi Kumar', email='ravi@example.com', password=pwd,
                     created_at=datetime.utcnow() - timedelta(days=60))
        user2 = User(name='Priya Sharma', email='priya@example.com', password=pwd,
                     created_at=datetime.utcnow() - timedelta(days=30))

        db.session.add_all([admin, user1, user2])
        db.session.flush()

        # ── Books ────────────────────────────────────────
        print('[+] Creating books...')
        books_data = [
            {
                'title': 'The Great Gatsby',
                'author': 'F. Scott Fitzgerald',
                'price': 299.00,
                'description': 'A masterpiece of American fiction set in the Jazz Age, exploring themes of wealth, love, and the American Dream through the eyes of narrator Nick Carraway.',
                'image_url': 'https://covers.openlibrary.org/b/id/8432047-L.jpg'
            },
            {
                'title': 'To Kill a Mockingbird',
                'author': 'Harper Lee',
                'price': 349.00,
                'description': 'A gripping tale of racial injustice in the Deep South, seen through the innocent eyes of young Scout Finch as her father defends a Black man accused of a crime.',
                'image_url': 'https://covers.openlibrary.org/b/id/8228691-L.jpg'
            },
            {
                'title': '1984',
                'author': 'George Orwell',
                'price': 275.00,
                'description': 'A dystopian masterpiece about a totalitarian society where Big Brother watches everything. A chilling exploration of surveillance, propaganda, and truth.',
                'image_url': 'https://covers.openlibrary.org/b/id/7222246-L.jpg'
            },
            {
                'title': 'Pride and Prejudice',
                'author': 'Jane Austen',
                'price': 249.00,
                'description': 'The beloved romantic comedy of manners following the spirited Elizabeth Bennet and the proud Mr. Darcy in Regency-era England.',
                'image_url': 'https://covers.openlibrary.org/b/id/12645114-L.jpg'
            },
            {
                'title': 'Sapiens: A Brief History of Humankind',
                'author': 'Yuval Noah Harari',
                'price': 499.00,
                'description': 'A groundbreaking narrative of humanity\'s creation and evolution, examining how biology and history have defined our understanding of what it means to be human.',
                'image_url': 'https://covers.openlibrary.org/b/id/8409647-L.jpg'
            },
            {
                'title': 'The Alchemist',
                'author': 'Paulo Coelho',
                'price': 225.00,
                'description': 'An enchanting tale of Santiago, an Andalusian shepherd boy who journeys to Egypt searching for treasure, learning about the Language of the World along the way.',
                'image_url': 'https://covers.openlibrary.org/b/id/6543958-L.jpg'
            },
            {
                'title': 'Atomic Habits',
                'author': 'James Clear',
                'price': 450.00,
                'description': 'A revolutionary guide to building good habits and breaking bad ones. Packed with evidence-based strategies for making small changes that deliver remarkable results.',
                'image_url': 'https://covers.openlibrary.org/b/id/10958382-L.jpg'
            },
            {
                'title': 'Dune',
                'author': 'Frank Herbert',
                'price': 399.00,
                'description': 'The epic sci-fi saga set on the desert planet Arrakis. A story of politics, religion, ecology, and human potential that has inspired generations.',
                'image_url': 'https://covers.openlibrary.org/b/id/11430898-L.jpg'
            },
            {
                'title': 'The Kite Runner',
                'author': 'Khaled Hosseini',
                'price': 325.00,
                'description': 'A powerful story of friendship, betrayal, and redemption set against the backdrop of Afghanistan\'s tumultuous history from the monarchy to the Taliban regime.',
                'image_url': 'https://covers.openlibrary.org/b/id/8232496-L.jpg'
            },
            {
                'title': 'Thinking, Fast and Slow',
                'author': 'Daniel Kahneman',
                'price': 475.00,
                'description': 'Nobel laureate Daniel Kahneman reveals how two systems of thinking — fast intuition and slow logic — shape our judgment, decisions, and behavior.',
                'image_url': 'https://covers.openlibrary.org/b/id/7327626-L.jpg'
            },
        ]

        book_objects = []
        for bd in books_data:
            book = Book(**bd, created_at=datetime.utcnow() - timedelta(days=random.randint(10, 80)))
            book_objects.append(book)
            db.session.add(book)

        db.session.flush()

        # ── Sample Orders ────────────────────────────────
        print('[+] Creating sample orders...')
        payment_methods = ['card', 'upi', 'cod']

        for i, user in enumerate([user1, user2]):
            for j in range(random.randint(2, 4)):
                days_ago = random.randint(1, 60)
                order_date = datetime.utcnow() - timedelta(days=days_ago)
                selected_books = random.sample(book_objects, random.randint(1, 3))

                total = sum(b.price * random.randint(1, 2) for b in selected_books)
                inv_num = f'INV-{order_date.strftime("%Y%m%d")}-{i * 10 + j + 1:04d}'

                order = Order(
                    user_id=user.id,
                    total_amount=round(total, 2),
                    payment_method=random.choice(payment_methods),
                    payment_status='completed',
                    order_status=random.choice(['placed', 'shipped', 'delivered']),
                    invoice_number=inv_num,
                    created_at=order_date
                )
                db.session.add(order)
                db.session.flush()

                for book in selected_books:
                    qty = random.randint(1, 2)
                    oi = OrderItem(
                        order_id=order.id,
                        book_id=book.id,
                        quantity=qty,
                        price=book.price
                    )
                    db.session.add(oi)

        db.session.commit()

        # Print summary
        print('\n[OK] Database seeded successfully!')
        print(f'   Users:  {User.query.count()} (admin: admin@bookhaven.com / password123)')
        print(f'   Books:  {Book.query.count()}')
        print(f'   Orders: {Order.query.count()}')
        print(f'\n[*] Test accounts:')
        print(f'   Admin:  admin@bookhaven.com  / password123')
        print(f'   User 1: ravi@example.com     / password123')
        print(f'   User 2: priya@example.com    / password123')


if __name__ == '__main__':
    seed()
