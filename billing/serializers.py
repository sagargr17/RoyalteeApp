# billing/serializers.py
from rest_framework import serializers
from .models import Invoice

class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = ['id', 'customer_name', 'amount', 'created_at']
        read_only_fields = ['id', 'created_at']