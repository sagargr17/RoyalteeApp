# billing/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import Customer, Invoice, Slot
from django.db import connection # Import connection to check schema
from unfold.admin import ModelAdmin # Ensuring Unfold is used


class TenantModelMixin(ModelAdmin):
    """Mixin to ensure models are completely hidden and inaccessible on the public schema."""
    def has_module_permission(self, request):
        return connection.schema_name != 'public'

    def has_view_permission(self, request, obj=None):
        return connection.schema_name != 'public'

    def has_add_permission(self, request):
        return connection.schema_name != 'public'

    def has_change_permission(self, request, obj=None):
        return connection.schema_name != 'public'

    def has_delete_permission(self, request, obj=None):
        return connection.schema_name != 'public'





@admin.register(Slot)
class SlotAdmin(TenantModelMixin):
    list_display = ('title', 'date', 'start_time', 'end_time', 'status', 'booked_by')
    list_filter = ('status', 'date')
    search_fields = ('title',)
    list_editable = ('status',)
    readonly_fields = ('booked_by',)
    ordering = ('date', 'start_time')
    



@admin.register(Invoice)
class InvoiceAdmin(TenantModelMixin):
    list_display = ('id', 'customer', 'slot', 'amount', 'created_at')
    autocomplete_fields = ['customer']
    search_fields = ('customer__name', 'customer__customer_code')
    list_filter = ('created_at',)


@admin.register(Customer)
class CustomerAdmin(TenantModelMixin):
    list_display = ('customer_code', 'name', 'access_pin', 'qr_preview')
    readonly_fields = ('customer_code', 'access_pin', 'qr_preview_large')
    search_fields = ('customer_code', 'name', 'email')

    def qr_preview(self, obj):
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