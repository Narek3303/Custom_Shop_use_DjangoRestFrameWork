from io import BytesIO
from django.template.loader import render_to_string
from weasyprint import HTML, CSS
from django.conf import settings
import os
from datetime import datetime, timedelta
import uuid


def generate_invoice_number():
    """Generate unique invoice number with date prefix"""
    return f"INV-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"


def generate_invoice_pdf(order, save_to_file=False):
    """Generate PDF invoice for an order"""
    from orders.models import Invoice

    # Create or get invoice
    invoice, created = Invoice.objects.get_or_create(
        order=order,
        defaults={
            'due_date': datetime.now() + timedelta(days=14)
        }
    )

    # Prepare context
    context = {
        'invoice': invoice,
        'order': order,
        'items': order.items.all(),
        'company': {
            'name': settings.COMPANY_NAME,
            'address': settings.COMPANY_ADDRESS,
            'phone': settings.COMPANY_PHONE,
            'email': settings.COMPANY_EMAIL,
            'tax_id': settings.COMPANY_TAX_ID,
            'logo': settings.COMPANY_LOGO_URL
        },
        'today': datetime.now().strftime("%B %d, %Y"),
        'due_date': invoice.due_date.strftime("%B %d, %Y")
    }

    # Render HTML
    html_string = render_to_string('orders/invoice_pdf.html', context)

    # CSS files (absolute paths)
    css_files = [
        os.path.join(settings.STATIC_ROOT, 'orders/css/pdf_styles.css'),
        CSS(string='@page { size: A4; margin: 1.5cm; }')
    ]

    # Generate PDF
    html = HTML(
        string=html_string,
        base_url=settings.BASE_DIR  # For static files
    )
    pdf_bytes = html.write_pdf(stylesheets=css_files)

    # Save to file if requested
    if save_to_file:
        file_path = os.path.join(settings.MEDIA_ROOT, 'invoices', f'invoice_{invoice.invoice_number}.pdf')
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'wb') as f:
            f.write(pdf_bytes)
        invoice.pdf_file.name = f'invoices/invoice_{invoice.invoice_number}.pdf'
        invoice.save()

    return pdf_bytes, invoice