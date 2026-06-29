# billing/models.py

from django.db import models
import uuid


class Customer(models.Model):
    customer_code = models.CharField(max_length=20, unique=True, editable=False, blank=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.customer_code:
            self.customer_code = self.generate_customer_code()
        super().save(*args, **kwargs)

    def generate_customer_code(self):
        # Format: CUST-XXXXXX (6-character unique suffix)
        while True:
            code = f"CUST-{uuid.uuid4().hex[:6].upper()}"
            if not Customer.objects.filter(customer_code=code).exists():
                return code

    def __str__(self):
        return f"{self.customer_code} — {self.name}"


class Invoice(models.Model):    
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='invoices')
    customer_name = models.CharField(max_length=100)  # kept for backward compatibility, see note below
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    remarks = models.TextField(max_length=250)

    def __str__(self):
        return f"Invoice #{self.id} — {self.customer.name}"