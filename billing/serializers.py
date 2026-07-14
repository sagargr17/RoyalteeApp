# billing/serializers.py
from rest_framework import serializers
from .models import Customer, Invoice, Slot


class SlotSerializer(serializers.ModelSerializer):
    is_available = serializers.ReadOnlyField()

    class Meta:
        model = Slot
        fields = [
            'id', 'title', 'date', 'start_time',
            'end_time', 'status', 'is_available',
            'booked_by', 'created_at'
        ]
        read_only_fields = ['id', 'status', 'booked_by', 'created_at']


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['id', 'customer_code', 'name', 'email', 'phone', 'created_at']
        read_only_fields = ['id', 'customer_code', 'created_at']




class InvoiceSerializer(serializers.ModelSerializer):
    customer = serializers.PrimaryKeyRelatedField(queryset=Customer.objects.all())
    customer_detail = CustomerSerializer(source='customer', read_only=True)
    slot = serializers.PrimaryKeyRelatedField(
        queryset=Slot.objects.filter(status='booked'),
        allow_null=True,
        required=False
    )
    slot_detail = SlotSerializer(source='slot', read_only=True)

    class Meta:
        model = Invoice
        fields = [
            'id', 'customer', 'customer_detail',
            'slot', 'slot_detail',
            'amount', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value

    def validate(self, data):
        slot = data.get('slot')
        customer = data.get('customer')
        if slot and slot.booked_by != customer:
            raise serializers.ValidationError(
                "This slot is not booked by the selected customer."
            )
        return data