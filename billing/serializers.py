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
        queryset=Slot.objects.filter(status='available'),
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

    def validate_slot(self, slot):
        if slot and not slot.is_available:
            raise serializers.ValidationError("This slot is already booked or cancelled.")
        return slot

    def create(self, validated_data):
        slot = validated_data.get('slot')
        invoice = super().create(validated_data)

        # mark slot as booked when invoice is created with a slot
        if slot:
            slot.status = 'booked'
            slot.booked_by = validated_data['customer']
            slot.save()

        return invoice