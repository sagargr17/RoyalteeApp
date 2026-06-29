# billing/views.py
from rest_framework import viewsets
from .models import Invoice
from .serializers import InvoiceSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import AccessToken
import datetime
from .models import Customer, Invoice
from .serializers import InvoiceSerializer



class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.all()  # automatically scoped to current schema
    serializer_class = InvoiceSerializer
    
    
           
class VerifyPinView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        customer_code = request.data.get('customer_code')
        pin = request.data.get('access_pin')

        if not customer_code or not pin:
            return Response({'error': 'customer_code and access_pin are required.'}, status=400)

        try:
            customer = Customer.objects.get(customer_code=customer_code, access_pin=pin)
        except Customer.DoesNotExist:
            return Response({'error': 'Invalid code or PIN.'}, status=status.HTTP_400_BAD_REQUEST)

        token = AccessToken()
        token['customer_id'] = customer.id
        token['customer_code'] = customer.customer_code
        token['token_type'] = 'customer_access'
        token.set_exp(lifetime=datetime.timedelta(minutes=15))

        return Response({
            'access': str(token),
            'customer_name': customer.name,
        })


class MyInvoicesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        token = request.auth
        if token.get('token_type') != 'customer_access':
            return Response({'error': 'Invalid token type.'}, status=403)

        customer_id = token.get('customer_id')
        invoices = Invoice.objects.filter(customer_id=customer_id).select_related('customer')

        return Response({
            'customer_code': token.get('customer_code'),
            'invoice_count': invoices.count(),
            'invoices': InvoiceSerializer(invoices, many=True).data,
        })