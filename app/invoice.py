import os
from flask import Blueprint, send_file, current_app, abort
from flask_login import login_required, current_user
from app.models import Order

invoice_bp = Blueprint('invoice', __name__)


def generate_pdf_invoice(order):
    """Generate a PDF invoice for the given order using ReportLab."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT

    invoice_dir = current_app.config['INVOICE_FOLDER']
    os.makedirs(invoice_dir, exist_ok=True)
    filepath = os.path.join(invoice_dir, f'{order.invoice_number}.pdf')

    doc = SimpleDocTemplate(filepath, pagesize=A4,
                            leftMargin=20 * mm, rightMargin=20 * mm,
                            topMargin=20 * mm, bottomMargin=20 * mm)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('InvoiceTitle', parent=styles['Title'],
                                  fontSize=24, textColor=colors.HexColor('#1a1a2e'),
                                  spaceAfter=6)
    subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'],
                                     fontSize=10, textColor=colors.gray)
    heading_style = ParagraphStyle('SectionHead', parent=styles['Heading2'],
                                    fontSize=13, textColor=colors.HexColor('#16213e'),
                                    spaceBefore=14, spaceAfter=6)

    elements = []

    # Header
    elements.append(Paragraph('📚 BookHaven', title_style))
    elements.append(Paragraph('Online Book Store — Invoice', subtitle_style))
    elements.append(Spacer(1, 10 * mm))

    # Invoice meta
    meta_data = [
        ['Invoice Number:', order.invoice_number],
        ['Date:', order.created_at.strftime('%d %B %Y, %I:%M %p')],
        ['Customer:', order.user.name],
        ['Email:', order.user.email],
        ['Payment Method:', order.payment_method.upper()],
        ['Payment Status:', order.payment_status.capitalize()],
    ]
    meta_table = Table(meta_data, colWidths=[120, 350])
    meta_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#333')),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 8 * mm))

    # Items table
    elements.append(Paragraph('Order Items', heading_style))
    table_data = [['#', 'Book Title', 'Author', 'Qty', 'Price (₹)', 'Subtotal (₹)']]
    for i, item in enumerate(order.items, 1):
        table_data.append([
            str(i),
            item.book.title if item.book else 'N/A',
            item.book.author if item.book else 'N/A',
            str(item.quantity),
            f'{item.price:.2f}',
            f'{item.price * item.quantity:.2f}'
        ])
    table_data.append(['', '', '', '', 'Total:', f'₹{order.total_amount:.2f}'])

    items_table = Table(table_data, colWidths=[30, 180, 100, 40, 80, 80])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a1a2e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (3, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (4, 1), (-1, -1), 'RIGHT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -2), 0.5, colors.HexColor('#ddd')),
        ('FONTNAME', (4, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (4, -1), (-1, -1), 11),
        ('TOPPADDING', (0, -1), (-1, -1), 10),
        ('LINEABOVE', (4, -1), (-1, -1), 1.5, colors.HexColor('#1a1a2e')),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 15 * mm))

    # Footer
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'],
                                   fontSize=8, textColor=colors.gray,
                                   alignment=TA_CENTER)
    elements.append(Paragraph('Thank you for shopping with BookHaven!', footer_style))
    elements.append(Paragraph('This is a computer-generated invoice and does not require a signature.', footer_style))

    doc.build(elements)
    return filepath


@invoice_bp.route('/api/orders/<int:order_id>/invoice')
@login_required
def download_invoice(order_id):
    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first()
    if not order and current_user.is_admin:
        order = Order.query.get(order_id)
    if not order:
        abort(404)

    filepath = os.path.join(current_app.config['INVOICE_FOLDER'], f'{order.invoice_number}.pdf')
    if not os.path.exists(filepath):
        # Regenerate if missing
        generate_pdf_invoice(order)

    return send_file(filepath, as_attachment=True,
                     download_name=f'{order.invoice_number}.pdf',
                     mimetype='application/pdf')
