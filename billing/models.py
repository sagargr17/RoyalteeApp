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
    qr_code = models.ImageField(upload_to='', blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.customer_code:
            self.customer_code = self.generate_customer_code()
        if not self.access_pin:
            self.access_pin = self.generate_access_pin()
        super().save(*args, **kwargs)
        # generate QR after save so we have a pk and customer_code
        if not self.qr_code:
            self.generate_and_save_qr()

    def generate_customer_code(self):
        while True:
            code = f"CUST-{uuid.uuid4().hex[:6].upper()}"
            if not Customer.objects.filter(customer_code=code).exists():
                return code

    def generate_access_pin(self):
        while True:
            pin = str(random.randint(1000, 9999))
            if not Customer.objects.filter(access_pin=pin).exists():
                return pin

    def generate_and_save_qr(self):
        try:
            import qrcode
            from io import BytesIO
            from django.core.files.base import ContentFile

            url = f"http://localhost:8000/verify/?c={self.customer_code}"
            qr = qrcode.make(url)

            buffer = BytesIO()
            qr.save(buffer, format='PNG')
            buffer.seek(0)

            filename = f"qr_{self.customer_code}.png"

            # This properly writes the file to storage AND updates self.qr_code.name
            self.qr_code.save(filename, ContentFile(buffer.getvalue()), save=False)

            # Now persist just that field to the DB (avoids recursive full save())
            Customer.objects.filter(pk=self.pk).update(qr_code=self.qr_code.name)

        except Exception as e:
            print(f"QR generation failed: {e}")



class Invoice(models.Model):    
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='invoices')
    customer_name = models.CharField(max_length=100)  # kept for backward compatibility, see note below
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    remarks = models.TextField(max_length=250)

    def __str__(self):
        return f"Invoice #{self.id} — {self.customer.name}"