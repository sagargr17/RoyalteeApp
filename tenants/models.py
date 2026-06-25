# tenants/models.py
from django.db import models
from django_tenants.models import TenantMixin, DomainMixin

class Client(TenantMixin):
    name = models.CharField(max_length=100)
    created_on = models.DateField(auto_now_add=True)
    plan = models.CharField(max_length=20, default='free')

    auto_create_schema = True  # creates schema automatically on save

class Domain(DomainMixin):
    pass