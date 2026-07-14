
from django.contrib import admin
from django.utils.html import format_html
from django.db import connection
from django import forms
from unfold.admin import ModelAdmin
from .models import Customer, Invoice, Slot, Booking


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



class BookingAdminForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['customer', 'slot', 'status', 'notes']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # on create — only show available slots
        # on edit — show all slots
        if not self.instance.pk:
            self.fields['slot'].queryset = Slot.objects.filter(
                status='available'
            ).order_by('date', 'start_time')
            self.fields['slot'].help_text = "Only available slots are shown"
        else:
            self.fields['slot'].queryset = Slot.objects.all().order_by(
                'date', 'start_time'
            )

        # readable slot label in dropdown
        self.fields['slot'].label_from_instance = lambda s: (
            f"{s.title}  |  {s.date}  |  "
            f"{s.start_time.strftime('%I:%M %p')} – "
            f"{s.end_time.strftime('%I:%M %p')}  |  "
            f"{s.get_status_display()}"
        )

    def clean(self):
        cleaned_data = super().clean()
        slot = cleaned_data.get('slot')

        # on new booking only — confirm slot is still available
        if not self.instance.pk and slot:
            if slot.status != 'available':
                raise forms.ValidationError(
                    f"Slot '{slot.title}' is no longer available. "
                    f"Current status: {slot.get_status_display()}"
                )
        return cleaned_data


@admin.register(Booking)
class BookingAdmin(TenantModelMixin):
    form = BookingAdminForm
    list_display = (
        'id', 'customer', 'slot_info',
        'status', 'slot_status_badge', 'created_at'
    )
    list_filter = ('status', 'slot__date', 'created_at')
    search_fields = (
        'customer__name',
        'customer__customer_code',
        'slot__title',
    )
    readonly_fields = ('created_at', 'updated_at', 'slot_current_status')
    autocomplete_fields = ['customer']
    list_per_page = 25
    ordering = ('-created_at',)

    fieldsets = (
        ('Booking Details', {
            'fields': ('customer', 'slot', 'status', 'notes')
        }),
        ('Slot Info', {
            'fields': ('slot_current_status',),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def slot_info(self, obj):
        return (
            f"{obj.slot.title}  |  "
            f"{obj.slot.date}  |  "
            f"{obj.slot.start_time.strftime('%I:%M %p')}"
        )
    slot_info.short_description = "Slot"

    def slot_status_badge(self, obj):
        colors = {
            'available': '#28a745',
            'booked': '#fd7e14',
            'cancelled': '#dc3545',
        }
        color = colors.get(obj.slot.status, 'grey')
        return format_html(
            '<strong style="color: {}">⬤ {}</strong>',
            color,
            obj.slot.get_status_display()
        )
    slot_status_badge.short_description = "Slot Status"

    def slot_current_status(self, obj):
        if obj.pk:
            colors = {
                'available': '#28a745',
                'booked': '#fd7e14',
                'cancelled': '#dc3545',
            }
            color = colors.get(obj.slot.status, 'grey')
            return format_html(
                '<strong style="color: {}">⬤ {}</strong> — {}  |  {} to {}',
                color,
                obj.slot.get_status_display(),
                obj.slot.date,
                obj.slot.start_time.strftime('%I:%M %p'),
                obj.slot.end_time.strftime('%I:%M %p'),
            )
        return "—"
    slot_current_status.short_description = "Current Slot Status"

    def save_model(self, request, obj, form, change):
        try:
            super().save_model(request, obj, form, change)
        except ValueError as e:
            from django.contrib import messages
            self.message_user(request, str(e), level=messages.ERROR)
        def get_queryset(self, request):
            qs = super().get_queryset(request)
            # if no status filter is applied, default to confirmed only
            if 'status__exact' not in request.GET:
                return qs.filter(status='confirmed')
            return qs




@admin.register(Slot)
class SlotAdmin(TenantModelMixin):
    list_display = (
        'title', 'date', 'start_time', 'end_time',
        'status_badge', 'booked_by', 'invoice_count', 'booking_count'
    )
    list_filter = ('status', 'date')
    search_fields = ('title',)
    readonly_fields = ('booked_by', 'invoice_count', 'booking_count')
    ordering = ('date', 'start_time')

    def status_badge(self, obj):
        colors = {
            'available': '#28a745',
            'booked': '#fd7e14',
            'cancelled': '#dc3545',
        }
        color = colors.get(obj.status, 'grey')
        return format_html(
            '<strong style="color: {}">⬤ {}</strong>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = "Status"

    def invoice_count(self, obj):
        return obj.invoices.count()
    invoice_count.short_description = "Invoices"

    def booking_count(self, obj):
        return obj.bookings.count()
    booking_count.short_description = "Total Bookings"


# billing/admin.py

@admin.register(Invoice)
class InvoiceAdmin(TenantModelMixin):
    list_display = ('id', 'customer', 'slot_info', 'amount', 'created_at')
    autocomplete_fields = ['customer']
    search_fields = ('customer__name', 'customer__customer_code')
    list_filter = ('created_at',)

    def slot_info(self, obj):
        if obj.slot:
            return (
                f"{obj.slot.title} | "
                f"{obj.slot.date} | "
                f"{obj.slot.start_time.strftime('%I:%M %p')}"
            )
        return "—"
    slot_info.short_description = "Slot Used"

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'slot':
            kwargs['queryset'] = Slot.objects.filter(status='booked')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # show confirmation message after slot is freed
        if not change and obj.slot:
            from django.contrib import messages
            self.message_user(
                request,
                f"Invoice created. Slot '{obj.slot.title}' is now available again.",
                level=messages.SUCCESS
            )
        
@admin.register(Customer)
class CustomerAdmin(TenantModelMixin):
    list_display = ('customer_code', 'name', 'access_pin', 'qr_preview')
    readonly_fields = ('customer_code', 'access_pin', 'qr_preview_large')
    search_fields = ('customer_code', 'name', 'email')

    def qr_preview(self, obj):
        if obj.qr_code and hasattr(obj.qr_code, 'url'):
            try:
                return format_html(
                    '<img src="{}" width="40" />', obj.qr_code.url
                )
            except Exception:
                return "—"
        return "—"
    qr_preview.short_description = "QR"

    def qr_preview_large(self, obj):
        if obj.qr_code and hasattr(obj.qr_code, 'url'):
            try:
                return format_html(
                    '<img src="{}" width="200" /><br/>'
                    '<strong>PIN: {}</strong><br/>'
                    '<a href="{}" download>Download QR</a>',
                    obj.qr_code.url, obj.access_pin, obj.qr_code.url
                )
            except Exception:
                return f"PIN: {obj.access_pin} (QR generation failed)"
        return f"PIN: {obj.access_pin} (QR not generated yet)"
    qr_preview_large.short_description = "QR Code"