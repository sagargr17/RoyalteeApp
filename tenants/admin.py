from django.contrib import admin
from .models import Client, Domain

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('schema_name', 'name', 'plan', 'created_on', 'is_active')
    list_editable = ('plan', 'is_active')
    search_fields = ('name', 'schema_name')
    actions = ['suspend_tenant', 'activate_tenant']

    def suspend_tenant(self, request, queryset):
        queryset.update(is_active=False)
    suspend_tenant.short_description = "Suspend selected tenants"

    def activate_tenant(self, request, queryset):
        queryset.update(is_active=True)
    activate_tenant.short_description = "Activate selected tenants"

@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ('domain', 'tenant', 'is_primary')