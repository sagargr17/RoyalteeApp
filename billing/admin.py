# billing/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import Customer, Invoice


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
        if obj.qr_code:
            return format_html('<img src="{}" width="40" />', obj.qr_code.url)
        return "—"

    def qr_preview_large(self, obj):
        if obj.qr_code:
            return format_html(
                '<img src="{}" width="200" /><p>PIN: <strong>{}</strong></p>',
                obj.qr_code.url, obj.access_pin
            )
        return "Not generated yet"