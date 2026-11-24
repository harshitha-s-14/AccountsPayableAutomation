from django.contrib import admin
from .models import Invoice

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("id", "invoice_number", "vendor", "status", "uploaded_at")
    search_fields = ("invoice_number", "vendor__vendor_name")
    list_filter = ("status",)
