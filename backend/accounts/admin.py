from django.contrib import admin
from .models import Invoice, ApprovalRule


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("id", "invoice_number", "vendor", "status", "uploaded_at")
    search_fields = ("invoice_number", "vendor__vendor_name")
    list_filter = ("status",)


@admin.register(ApprovalRule)
class ApprovalRuleAdmin(admin.ModelAdmin):
    list_display = (
        "rule_name",
        "approval_level",
        "minimum_amount",
        "maximum_amount",
        "approver_role",
        "is_active",
    )
    list_filter = ("approval_level", "approver_role", "is_active")