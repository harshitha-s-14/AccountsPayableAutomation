from django.db import models


class Vendor(models.Model):

    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('PENDING', 'Pending'),
    ]

    vendor_name = models.CharField(max_length=200)

    email = models.EmailField(unique=True)

    phone = models.CharField(max_length=15)

    address = models.TextField()

    gst_number = models.CharField(
        max_length=15,
        unique=True,
        null=True,
        blank=True
    )

    tax_identification_number = models.CharField(
        max_length=50,
        blank=True
    )

    # Vendor bank details
    bank_account_name = models.CharField(
        max_length=200,
        blank=True
    )

    bank_account_number = models.CharField(
        max_length=30,
        blank=True
    )

    bank_name = models.CharField(
        max_length=100,
        blank=True
    )

    ifsc_code = models.CharField(
        max_length=11,
        blank=True
    )

    branch_name = models.CharField(
        max_length=100,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.vendor_name
class Invoice(models.Model):

    STATUS_CHOICES = [
        ('UPLOADED', 'Uploaded'),
        ('PROCESSING', 'Processing'),
        ('PROCESSED', 'Processed'),
        ('FAILED', 'Failed'),
    ]

    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.CASCADE,
        related_name='invoices'
    )

    invoice_number = models.CharField(max_length=100)

    invoice_file = models.FileField(upload_to='invoices/')

    invoice_date = models.DateField(null=True, blank=True)

    due_date = models.DateField(null=True, blank=True)

    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='UPLOADED'
    )

    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.invoice_number
class OCRExtraction(models.Model):

    invoice = models.OneToOneField(
        Invoice,
        on_delete=models.CASCADE,
        related_name='ocr_extraction'
    )

    extracted_text = models.TextField(
        blank=True
    )

    extracted_data = models.JSONField(
        default=dict,
        blank=True
    )

    extraction_status = models.CharField(
        max_length=20,
        default='PENDING'
    )

    processed_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"OCR - {self.invoice.invoice_number}"

class InvoiceLineItem(models.Model):

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='line_items'
    )

    description = models.CharField(max_length=255)

    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=1
    )

    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.description
class PurchaseOrder(models.Model):

    po_number = models.CharField(max_length=100, unique=True)

    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.CASCADE,
        related_name='purchase_orders'
    )

    po_date = models.DateField()

    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    status = models.CharField(
        max_length=20,
        default='OPEN'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.po_number


class PurchaseOrderLineItem(models.Model):

    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name='line_items'
    )

    description = models.CharField(max_length=255)

    quantity = models.DecimalField(max_digits=10, decimal_places=2)

    unit_price = models.DecimalField(max_digits=12, decimal_places=2)

    amount = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return self.description


class GoodsReceiptNote(models.Model):

    grn_number = models.CharField(max_length=100, unique=True)

    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name='goods_receipts'
    )

    received_date = models.DateField()

    status = models.CharField(
        max_length=20,
        default='RECEIVED'
    )

    def __str__(self):
        return self.grn_number


class GRNLineItem(models.Model):

    grn = models.ForeignKey(
        GoodsReceiptNote,
        on_delete=models.CASCADE,
        related_name='line_items'
    )

    description = models.CharField(max_length=255)

    quantity_received = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    def __str__(self):
        return self.description

class ApprovalRule(models.Model):

    rule_name = models.CharField(max_length=150)
    approval_level = models.PositiveIntegerField(default=1)

    minimum_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    maximum_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )

    approver_role = models.CharField(max_length=100)

    escalation_after_hours = models.PositiveIntegerField(default=48)

    escalation_role = models.CharField(
        max_length=100,
        blank=True,
        default='MANAGER'
    )

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.rule_name


class ApprovalRequest(models.Model):

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='approval_requests'
    )

    approval_rule = models.ForeignKey(
        ApprovalRule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    approver_role = models.CharField(max_length=100)

    original_approver_role = models.CharField(
        max_length=100,
        blank=True,
        default=''
    )

    is_escalated = models.BooleanField(default=False)

    escalated_at = models.DateTimeField(
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )

    comments = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Approval - {self.invoice.invoice_number}"



class ApprovalAction(models.Model):

    approval_request = models.ForeignKey(
        ApprovalRequest,
        on_delete=models.CASCADE,
        related_name='actions'
    )

    action = models.CharField(max_length=20)

    comments = models.TextField(blank=True)

    action_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.action


class AuditLog(models.Model):

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs'
    )

    action = models.CharField(max_length=200)

    description = models.TextField(blank=True)

    performed_by = models.CharField(
        max_length=150,
        default='System'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.action
class Payment(models.Model):

    PAYMENT_STATUS = [
        ('REQUESTED', 'Requested'),
        ('PROCESSING', 'Processing'),
        ('PAID', 'Paid'),
        ('FAILED', 'Failed'),
    ]

    invoice = models.OneToOneField(
        Invoice,
        on_delete=models.CASCADE,
        related_name='payment'
    )

    payment_reference = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=50, default='BANK_TRANSFER')
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS,
        default='REQUESTED'
    )
    payment_date = models.DateField(null=True, blank=True)
    bank_reference = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.payment_reference
