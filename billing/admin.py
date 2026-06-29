from django.contrib import admin
from .models import Invoice,Customer

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('customer_name', 'amount', 'created_at')
    search_fields = ('customer_name',)

admin.site.register(Customer)