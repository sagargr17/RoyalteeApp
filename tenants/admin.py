# # tenants/admin.py
# from django import forms
# from django.contrib import admin
# from django.contrib.auth import get_user_model
# from django_tenants.utils import schema_context
# from .models import Client, Domain
# from django.db import connection


# class ClientAdminForm(forms.ModelForm):
#     admin_email = forms.EmailField(
#         label="Tenant admin email",
#         help_text="Login email for this tenant's first user"
#     )
#     admin_password = forms.CharField(
#         label="Tenant admin password",
#         widget=forms.PasswordInput,
#         help_text="They can change this after first login"
#     )

#     class Meta:
#         model = Client
#         fields = ['schema_name', 'name', 'plan']


# @admin.register(Client)
# class ClientAdmin(admin.ModelAdmin):
#     form = ClientAdminForm
#     list_display = ('schema_name', 'name', 'plan', 'created_on', 'is_active')
#     list_editable = ('plan', 'is_active')
#     search_fields = ('name', 'schema_name')

#     def save_model(self, request, obj, form, change):
#         super().save_model(request, obj, form, change)  # saves Client → triggers auto_create_schema

#         if not change:  # only on CREATE, not when editing an existing tenant
#             # Auto-create the domain
#             Domain.objects.create(
#                 domain=f"{obj.schema_name}.yourapp.com",
#                 tenant=obj,
#                 is_primary=True,
#             )

#             # Create the first user, inside the new tenant's schema
#             with schema_context(obj.schema_name):
#                 User = get_user_model()
#                 User.objects.create_superuser(
#                     username=form.cleaned_data['admin_email'],
#                     email=form.cleaned_data['admin_email'],
#                     password=form.cleaned_data['admin_password'],
#                 )
                
                
#     def has_module_permission(self, request):
#         # Only show this in the public schema — hide entirely on tenant schemas
#         return connection.schema_name == 'public'

#     def has_view_permission(self, request, obj=None):
#         return connection.schema_name == 'public'

#     def has_add_permission(self, request):
#         return connection.schema_name == 'public'

#     def has_change_permission(self, request, obj=None):
#         return connection.schema_name == 'public'

#     def has_delete_permission(self, request, obj=None):
#         return connection.schema_name == 'public'


# @admin.register(Domain)
# class DomainAdmin(admin.ModelAdmin):
#     list_display = ('domain', 'tenant', 'is_primary')
    
# tenants/admin.py
from django import forms
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db import connection
from django_tenants.utils import schema_context
from .models import Client, Domain


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
class ClientAdmin(admin.ModelAdmin):
    form = ClientAdminForm
    list_display = ('schema_name', 'name', 'plan', 'created_on', 'is_active')
    list_editable = ('plan', 'is_active')
    search_fields = ('name', 'schema_name')

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)  # saves Client → triggers auto_create_schema

        if not change:  # only on CREATE, not when editing an existing tenant
            # Auto-create the domain
            Domain.objects.create(
                domain=f"{obj.schema_name}.localhost",
                tenant=obj,
                is_primary=True,
            )

            print(form.cleaned_data['admin_email'])
            # Create the first user, inside the new tenant's schema —
            # staff but NOT superuser, so we can scope their permissions
            with schema_context(obj.schema_name):
                User = get_user_model()
                user = User.objects.create_user(
                    username=form.cleaned_data['admin_email'],
                    email=form.cleaned_data['admin_email'],
                    password=form.cleaned_data['admin_password'],
                    is_staff=True,
                    is_superuser=False,
                )

                # Restrict this user to ONLY the Invoice model
                from billing.models import Invoice
                content_type = ContentType.objects.get_for_model(Invoice)
                permissions = Permission.objects.filter(content_type=content_type)
                user.user_permissions.set(permissions)

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


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
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
    