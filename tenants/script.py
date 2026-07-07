from django_tenants.utils import schema_context
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.management import create_permissions
from django.apps import apps

with schema_context('nawagulmeli'):
    from billing.models import Customer, Invoice, Slot

    # force create all content types and permissions for billing app
    create_permissions(apps.get_app_config('billing'), verbosity=0)

    # get content types
    customer_ct, _ = ContentType.objects.get_or_create(app_label='billing', model='customer')
    invoice_ct, _ = ContentType.objects.get_or_create(app_label='billing', model='invoice')
    slot_ct, _ = ContentType.objects.get_or_create(app_label='billing', model='slot')

    permissions = Permission.objects.filter(
        content_type__in=[customer_ct, invoice_ct, slot_ct]
    )
    print(f"Permissions found: {list(permissions.values_list('codename', flat=True))}")

    User = get_user_model()
    for user in User.objects.all():
        user.user_permissions.set(permissions)
        print(f"Assigned to: {user.username}")