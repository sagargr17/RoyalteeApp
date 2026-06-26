# billing/views.py
from rest_framework import viewsets
from .models import Invoice
from .serializers import InvoiceSerializer


class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.all()  # automatically scoped to current schema
    serializer_class = InvoiceSerializer
    
    
