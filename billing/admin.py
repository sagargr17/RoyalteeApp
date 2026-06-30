# billing/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import Customer, Invoice
from django_tenants.utils import schema_context
from django.contrib.auth import get_user_model
from tenants.models import  Domain


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'amount', 'created_at')
    autocomplete_fields = ['customer']
    search_fields = ('customer__name', 'customer__customer_code')




@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('customer_code', 'name', 'access_pin', 'qr_preview')
    readonly_fields = ('customer_code', 'access_pin', 'qr_preview_large')
    search_fields = ('customer_code', 'name', 'email')

    def qr_preview(self, obj):
        # safely check if field exists and has a value
        if obj.qr_code and hasattr(obj.qr_code, 'url'):
            try:
                return format_html('<img src="{}" width="40" />', obj.qr_code.url)
            except Exception:
                return "—"
        return "—"
    qr_preview.short_description = "QR"

    def qr_preview_large(self, obj):
        if obj.qr_code and hasattr(obj.qr_code, 'url'):
            try:
                return format_html(
                    '<img src="{}" width="200" /><br/><strong>PIN: {}</strong><br/>'
                    '<a href="{}" download>Download QR</a>',
                    obj.qr_code.url, obj.access_pin, obj.qr_code.url
                )
            except Exception:
                return f"PIN: {obj.access_pin} (QR generation failed)"
        return f"PIN: {obj.access_pin} (QR not generated yet)"
    qr_preview_large.short_description = "QR Code"