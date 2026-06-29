# billing/models.py

from django.db import models
import uuid
import random


class Customer(models.Model):
    customer_code = models.CharField(max_length=20, unique=True, editable=False, blank=True)
    access_pin = models.CharField(max_length=6, unique=True, editable=False, blank=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)  # no longer required for auth
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.customer_code:
            self.customer_code = self.generate_customer_code()
        super().save(*args, **kwargs)

    def generate_customer_code(self):
        while True:
            code = f"CUST-{uuid.uuid4().hex[:6].upper()}"
            if not Customer.objects.filter(customer_code=code).exists():
                return code
                
    def generate_access_pin(self):
        while True:
            pin = str(random.randint(1000, 9999))  # 4-digit PIN
            if not Customer.objects.filter(access_pin=pin).exists():
                return pin

    def __str__(self):
        return f"{self.customer_code} — {self.name}"                

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