from decimal import Decimal
import re


def descriptions_match(description1, description2):
    def normalize(text):
        words = re.findall(r"[a-z0-9]+", text.casefold())
        ignored = {"and", "or", "the", "of", "for", "a", "an"}
        return set(words) - ignored

    words1 = normalize(description1)
    words2 = normalize(description2)

    if words1 == words2:
        return True

    common_words = words1.intersection(words2)

    return (
        len(common_words) >= 2
        and len(common_words) / min(len(words1), len(words2)) >= 0.5
    )


def perform_po_matching(invoice, purchase_order, grn=None):

    results = {
        'invoice_number': invoice.invoice_number,
        'po_number': purchase_order.po_number,
        'two_way_matching': {},
        'three_way_matching': {},
        'overall_status': 'MATCHED'
    }

    tolerance = Decimal('0.01')

    # 1. Vendor validation
    vendor_match = invoice.vendor_id == purchase_order.vendor_id

    results['two_way_matching']['vendor_match'] = vendor_match

    # 2. Compare PO amount with invoice line-item subtotal
    invoice_items = list(invoice.line_items.all())
    po_items = list(purchase_order.line_items.all())

    invoice_amount = sum(
        (item.amount for item in invoice_items),
        Decimal('0')
    )

    po_amount = purchase_order.total_amount or Decimal('0')

    amount_difference = abs(invoice_amount - po_amount)
    amount_match = amount_difference <= tolerance

    results['two_way_matching']['amount_match'] = amount_match
    results['two_way_matching']['amount_difference'] = str(
        amount_difference
    )
    results['two_way_matching']['invoice_subtotal'] = str(invoice_amount)
    results['two_way_matching']['po_amount'] = str(po_amount)

    # 3. Line-item validation
    line_item_checks = []
    matched_invoice_indexes = set()

    if not po_items:
        results['two_way_matching']['line_item_error'] = (
            'Purchase order contains no line items.'
        )

    for po_item in po_items:

        matching_indexes = [
            index for index, item in enumerate(invoice_items)
            if index not in matched_invoice_indexes
            and descriptions_match(
                item.description,
                po_item.description
            )
        ]

        matching_items = [
            invoice_items[index] for index in matching_indexes
        ]

        matched_invoice_indexes.update(matching_indexes)

        invoice_quantity = sum(
            (item.quantity for item in matching_items),
            Decimal('0')
        )

        invoice_item_amount = sum(
            (item.amount for item in matching_items),
            Decimal('0')
        )

        quantity_match = (
            abs(invoice_quantity - po_item.quantity) <= tolerance
        )

        item_amount_match = (
            abs(invoice_item_amount - po_item.amount) <= tolerance
        )

        line_item_checks.append({
            'item': po_item.description,
            'po_quantity': str(po_item.quantity),
            'invoice_quantity': str(invoice_quantity),
            'po_amount': str(po_item.amount),
            'invoice_amount': str(invoice_item_amount),
            'quantity_match': quantity_match,
            'amount_match': item_amount_match,
            'matched': quantity_match and item_amount_match
        })

    # Detect unmatched invoice items
    extra_invoice_items = [
        item.description
        for index, item in enumerate(invoice_items)
        if index not in matched_invoice_indexes
    ]

    results['two_way_matching']['line_item_checks'] = line_item_checks
    results['two_way_matching']['extra_invoice_items'] = extra_invoice_items

    two_way_match = (
        vendor_match
        and amount_match
        and bool(po_items)
        and bool(invoice_items)
        and all(item['matched'] for item in line_item_checks)
        and not extra_invoice_items
    )

    if not two_way_match:
        results['overall_status'] = 'MISMATCHED'

    # 4. Three-way matching: PO vs GRN vs Invoice
    if grn:

        results['three_way_matching']['grn_number'] = grn.grn_number

        grn_match = (
            grn.purchase_order_id == purchase_order.id
            and grn.status == 'RECEIVED'
        )

        results['three_way_matching']['grn_match'] = grn_match

        quantity_checks = []
        grn_items = list(grn.line_items.all())

        if grn_match:

            for po_item in po_items:

                matching_grn_items = [
                    item for item in grn_items
                    if descriptions_match(
                        item.description,
                        po_item.description
                    )
                ]

                matching_invoice_items = [
                    item for item in invoice_items
                    if descriptions_match(
                        item.description,
                        po_item.description
                    )
                ]

                received_quantity = sum(
                    (item.quantity_received for item in matching_grn_items),
                    Decimal('0')
                )

                billed_quantity = sum(
                    (item.quantity for item in matching_invoice_items),
                    Decimal('0')
                )

                received_vs_ordered = (
                    received_quantity <= po_item.quantity
                )

                billed_vs_received = (
                    billed_quantity <= received_quantity
                )

                quantity_checks.append({
                    'item': po_item.description,
                    'ordered_quantity': str(po_item.quantity),
                    'received_quantity': str(received_quantity),
                    'billed_quantity': str(billed_quantity),
                    'received_vs_ordered': received_vs_ordered,
                    'billed_vs_received': billed_vs_received,
                    'matched': (
                        received_vs_ordered
                        and billed_vs_received
                    )
                })

        results['three_way_matching']['quantity_checks'] = quantity_checks

        three_way_match = (
            grn_match
            and bool(quantity_checks)
            and all(item['matched'] for item in quantity_checks)
        )

        results['three_way_matching']['overall_match'] = three_way_match

        if not three_way_match:
            results['overall_status'] = 'MISMATCHED'

    return results