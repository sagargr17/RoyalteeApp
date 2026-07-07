# billing/views.py
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import action
from rest_framework_simplejwt.tokens import AccessToken
import datetime
from .models import Customer, Invoice, Slot
from .serializers import CustomerSerializer, InvoiceSerializer, SlotSerializer


class SlotViewSet(viewsets.ModelViewSet):
    serializer_class = SlotSerializer

    def get_queryset(self):
        queryset = Slot.objects.all()
        # filter by availability if requested
        available = self.request.query_params.get('available')
        if available == 'true':
            queryset = queryset.filter(status='available')
        # filter by date if requested
        date = self.request.query_params.get('date')
        if date:
            queryset = queryset.filter(date=date)
        return queryset

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def cancel(self, request, pk=None):
        """Tenant staff can cancel a slot"""
        slot = self.get_object()
        if slot.status == 'cancelled':
            return Response({'error': 'Slot is already cancelled.'}, status=400)
        slot.status = 'cancelled'
        slot.booked_by = None
        slot.save()
        return Response({'message': 'Slot cancelled successfully.'})


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer


class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.select_related('customer', 'slot').all()
    serializer_class = InvoiceSerializer


class VerifyPinView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        customer_code = request.data.get('customer_code')
        pin = request.data.get('access_pin')

        if not customer_code or not pin:
            return Response(
                {'error': 'customer_code and access_pin are required.'},
                status=400
            )

        try:
            customer = Customer.objects.get(customer_code=customer_code, access_pin=pin)
        except Customer.DoesNotExist:
            return Response({'error': 'Invalid code or PIN.'}, status=400)

        token = AccessToken()
        token['customer_id'] = customer.id
        token['customer_code'] = customer.customer_code
        token['token_type'] = 'customer_access'
        token.set_exp(lifetime=datetime.timedelta(minutes=30))

        return Response({
            'access': str(token),
            'customer_name': customer.name,
        })


class MyInvoicesView(APIView):
    """Customer-facing — returns invoice count, details, and current slot booking"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        token = request.auth
        if token.get('token_type') != 'customer_access':
            return Response({'error': 'Invalid token type.'}, status=403)

        customer_id = token.get('customer_id')
        invoices = Invoice.objects.filter(
            customer_id=customer_id
        ).select_related('customer', 'slot')

        # check if customer has an active slot booking
        active_slot = None
        try:
            booked = Slot.objects.get(booked_by_id=customer_id, status='booked')
            active_slot = SlotSerializer(booked).data
        except Slot.DoesNotExist:
            pass

        return Response({
            'customer_code': token.get('customer_code'),
            'invoice_count': invoices.count(),
            'active_slot': active_slot,
            'invoices': InvoiceSerializer(invoices, many=True).data,
        })


class AvailableSlotsView(APIView):
    """
    Public endpoint — customer can check available slots
    before or after PIN verification
    """
    permission_classes = [AllowAny]

    def get(self, request):
        slots = Slot.objects.filter(status='available').order_by('date', 'start_time')
        date = request.query_params.get('date')
        if date:
            slots = slots.filter(date=date)
        return Response(SlotSerializer(slots, many=True).data)


class BookSlotView(APIView):
    """Customer books a slot after PIN verification"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        token = request.auth
        if token.get('token_type') != 'customer_access':
            return Response({'error': 'Invalid token type.'}, status=403)

        customer_id = token.get('customer_id')
        slot_id = request.data.get('slot_id')

        if not slot_id:
            return Response({'error': 'slot_id is required.'}, status=400)

        # check customer doesn't already have a booked slot
        if Slot.objects.filter(booked_by_id=customer_id, status='booked').exists():
            return Response(
                {'error': 'You already have an active slot booking.'},
                status=400
            )

        try:
            slot = Slot.objects.select_for_update().get(id=slot_id, status='available')
        except Slot.DoesNotExist:
            return Response(
                {'error': 'Slot not found or no longer available.'},
                status=400
            )

        from django.db import transaction
        with transaction.atomic():
            slot.status = 'booked'
            slot.booked_by_id = customer_id
            slot.save()

        return Response({
            'message': 'Slot booked successfully.',
            'slot': SlotSerializer(slot).data,
        })