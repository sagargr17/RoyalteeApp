# tenants/admin.py
from django import forms
from django.contrib import admin
from django.contrib.auth import get_user_model
# from django.contrib.auth.models import Permission
# from django.contrib.contenttypes.models import ContentType
from django.db import connection
from django_tenants.utils import schema_context
from .models import Client, Domain
from django_tenants.utils import get_public_schema_name
from unfold.admin import ModelAdmin # Import Unfold's class


class ClientAdminForm(forms.ModelForm):
    admin_email = forms.EmailField(
        label="Tenant admin email",
        help_text="Login email for this tenant's first user"
    )
    admin_password = forms.CharField(
        label="Tenant admin password",
        widget=forms.PasswordInput,
        help_text="They can change this after first login"
    )

    class Meta:
        model = Client
        fields = ['schema_name', 'name', 'plan']


@admin.register(Client)
class ClientAdmin(ModelAdmin):
    form = ClientAdminForm
    list_display = ('schema_name', 'name', 'plan', 'created_on', 'is_active')
    list_editable = ('plan', 'is_active')
    search_fields = ('name', 'schema_name')

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        if not change:
            Domain.objects.create(
                domain=f"{obj.schema_name}.192.168.100.100",
                tenant=obj,
                is_primary=True,
            )
            
            print("schema>>>",obj.schema_name)
            with schema_context(obj.schema_name):
                User = get_user_model()
                print("user", User)
                user = User.objects.create_user(
                    username=form.cleaned_data['admin_email'],
                    email=form.cleaned_data['admin_email'],
                    password=form.cleaned_data['admin_password'],
                    is_staff=True,
                    is_superuser=True,
                )

                from billing.models import Invoice, Customer,  Slot
                from django.contrib.contenttypes.models import ContentType
                from django.contrib.auth.models import Permission

                # get_or_create ensures content types exist
                # even on freshly created schemas
                customer_ct, _ = ContentType.objects.get_or_create(
                    app_label='billing', model='customer'
                )
                invoice_ct, _ = ContentType.objects.get_or_create(
                    app_label='billing', model='invoice'
                )
                slot_ct, _ = ContentType.objects.get_or_create(
                    app_label='billing', model='slot'
                )
                booking_ct, _ = ContentType.objects.get_or_create(app_label='billing', model='booking')

                permissions = Permission.objects.filter(
                    content_type__in=[customer_ct, invoice_ct,slot_ct,booking_ct]
                )

                # if permissions are empty, they haven't been created yet
                # — run a management command to create them first
                if not permissions.exists():
                    from django.contrib.auth.management import create_permissions
                    from django.apps import apps
                    create_permissions(apps.get_app_config('billing'), verbosity=0)
                    permissions = Permission.objects.filter(
                        content_type__in=[customer_ct, invoice_ct, booking_ct]
                    )

                user.user_permissions.set(permissions)
                print(f"Assigned {permissions.count()} permissions to {user.username}")
                
                

    # Restrict this admin section to the PUBLIC schema only
    def has_module_permission(self, request):
        return connection.schema_name == 'public'

    def has_view_permission(self, request, obj=None):
        return connection.schema_name == 'public'

    def has_add_permission(self, request):
        return connection.schema_name == 'public'

    def has_change_permission(self, request, obj=None):
        return connection.schema_name == 'public'

    def has_delete_permission(self, request, obj=None):
        return connection.schema_name == 'public'
    
    def has_delete_permission(self, request, obj=None):
        # Prevents deletion if the object matches the public schema name
        if obj and obj.schema_name == get_public_schema_name():
            return False
        return super().has_delete_permission(request, obj)
    
    
    
    


@admin.register(Domain)
class DomainAdmin(ModelAdmin):
    list_display = ('domain', 'tenant', 'is_primary')

    # Same restriction — Domain is also a public-only model
    def has_module_permission(self, request):
        return connection.schema_name == 'public'

    def has_view_permission(self, request, obj=None):
        return connection.schema_name == 'public'

    def has_add_permission(self, request):
        return connection.schema_name == 'public'

    def has_change_permission(self, request, obj=None):
        return connection.schema_name == 'public'

    def has_delete_permission(self, request, obj=None):
        return connection.schema_name == 'public'    
    