import re
from decimal import Decimal, InvalidOperation
from datetime import datetime
from pathlib import Path

import pymupdf as fitz
import pytesseract

from PIL import Image, ImageSequence


def extract_text_from_invoice(file_path):

    extracted_pages = []
    extension = Path(file_path).suffix.lower()

    if extension == '.pdf':

        document = fitz.open(file_path)

        try:
            for page in document:

                page_text = page.get_text()

                # Use OCR for scanned or nearly empty pages
                if len(page_text.strip()) < 30:

                    pix = page.get_pixmap(
                        dpi=300,
                        colorspace=fitz.csRGB,
                        alpha=False
                    )

                    image = Image.frombytes(
                        "RGB",
                        [pix.width, pix.height],
                        pix.samples
                    )

                    page_text = pytesseract.image_to_string(image)

                extracted_pages.append(page_text)

        finally:
            document.close()

    elif extension in ['.jpg', '.jpeg', '.png', '.tiff', '.tif']:

        image = Image.open(file_path)

        for frame in ImageSequence.Iterator(image):

            frame_image = frame.convert("RGB")

            page_text = pytesseract.image_to_string(frame_image)

            extracted_pages.append(page_text)

    else:
        raise ValueError("Unsupported invoice file format.")

    return "\n".join(extracted_pages)


def normalize_date(value):

    value = value.strip().replace(',', '')

    formats = [
        '%d/%m/%Y',
        '%d-%m-%Y',
        '%d.%m.%Y',
        '%d/%m/%y',
        '%d-%m-%y',
        '%Y-%m-%d',
        '%d %b %Y',
        '%d %B %Y',
        '%b %d %Y',
        '%B %d %Y'
    ]

    for date_format in formats:

        try:
            return datetime.strptime(
                value,
                date_format
            ).date().isoformat()

        except ValueError:
            continue

    return None


def clean_decimal(value):

    if not value:
        return None

    cleaned = re.sub(r'[^\d.]', '', str(value).replace(',', ''))

    try:
        return Decimal(cleaned)

    except InvalidOperation:
        return None


def extract_invoice_fields(text):

    fields = {
        "invoice_number": None,
        "invoice_date": None,
        "due_date": None,
        "gst_number": None,
        "total_amount": None,
        "line_items": [],
        "extraction_warnings": [],
        "extraction_confidence": 0
    }

    text = text.replace('\xa0', ' ')
    text = text.replace('\u20b9', 'Rs ')
    text = text.replace('â‚¹', 'Rs ')

    date_pattern = (
        r'(?:\d{1,2}[-/. ]'
        r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|'
        r'\d{1,2})'
        r'[-/. ]\d{2,4}|'
        r'\d{4}-\d{2}-\d{2}|'
        r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)'
        r'\s+\d{1,2},?\s+\d{4})'
    )

    patterns = {

        "invoice_number": (
            r'Invoice\s*(?:No\.?|Number|#)\s*[:\-]?\s*'
            r'([A-Z0-9][A-Z0-9/-]*)'
        ),

        "invoice_date": (
            r'Invoice\s*Date\s*[:\-]?\s*'
            r'(' + date_pattern + r')'
        ),

        "due_date": (
            r'Due\s*Date\s*[:\-]?\s*'
            r'(' + date_pattern + r')'
        ),

        "gst_number": (
            r'\b\d{2}[A-Z]{5}\d{4}[A-Z][A-Z0-9]Z[A-Z0-9]\b'
        ),

        "total_amount": (
            r'(?:Grand\s*Total|Total\s*Amount|'
            r'Net\s*Amount|Amount\s*Due|Invoice\s*Total)'
            r'\s*[:\-]?\s*(?:Rs\.?|INR)?\s*'
            r'([\d,]+(?:\.\d{1,2})?)'
        )
    }

    # Extract invoice header fields

    for field, pattern in patterns.items():

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if not match:
            continue

        value = match.group(0) if field == "gst_number" else match.group(1)

        if field in ["invoice_date", "due_date"]:

            value = normalize_date(value)

        elif field == "total_amount":

            amount = clean_decimal(value)

            value = str(amount.quantize(Decimal('0.01'))) if amount is not None else None

        fields[field] = value

    # Extract line items

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    ignored_headers = [
        'description',
        'quantity',
        'unit price',
        'amount',
        'total'
    ]

    def add_line_item(description, quantity, unit_price, amount):

        quantity_value = clean_decimal(quantity)
        price_value = clean_decimal(unit_price)
        amount_value = clean_decimal(amount)

        if (
            not description
            or quantity_value is None
            or price_value is None
            or amount_value is None
        ):
            return

        if quantity_value <= 0 or price_value < 0 or amount_value < 0:
            return

        fields["line_items"].append({
            "description": description.strip(),
            "quantity": str(quantity_value),
            "unit_price": str(price_value.quantize(Decimal('0.01'))),
            "amount": str(amount_value.quantize(Decimal('0.01')))
        })

    # Try tab-separated and pipe-separated table rows

    for line in lines:

        if '\t' in line:
            parts = [part.strip() for part in line.split('\t')]

        elif '|' in line:
            parts = [part.strip() for part in line.split('|')]

        else:
            continue

        if len(parts) < 4:
            continue

        if any(header in parts[0].lower() for header in ignored_headers):
            continue

        add_line_item(
            parts[0],
            parts[1],
            parts[2],
            parts[3]
        )

    # Fallback for values appearing on separate lines

    if not fields["line_items"]:

        for index in range(len(lines) - 3):

            description = lines[index]

            if any(
                header in description.lower()
                for header in ignored_headers
            ):
                continue

            add_line_item(
                description,
                lines[index + 1],
                lines[index + 2],
                lines[index + 3]
            )

    # Report missing fields

    mandatory_fields = [
        "invoice_number",
        "invoice_date",
        "total_amount"
    ]

    for field in mandatory_fields:

        if not fields[field]:

            fields["extraction_warnings"].append(
                f"Could not extract {field.replace('_', ' ')}."
            )

    if not fields["gst_number"]:

        fields["extraction_warnings"].append(
            "GSTIN was not detected."
        )

    if not fields["line_items"]:

        fields["extraction_warnings"].append(
            "No invoice line items were detected."
        )

    # Basic extraction completeness score
    fields["extraction_confidence"] = round(
        sum(bool(fields[field]) for field in mandatory_fields)
        / len(mandatory_fields) * 100
    )

    return fields