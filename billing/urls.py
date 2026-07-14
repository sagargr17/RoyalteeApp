# billing/urls.py
from rest_framework.routers import DefaultRouter
from .views import InvoiceViewSet

from django.urls import path
from .views import VerifyPinView, MyInvoicesView, AvailableSlotsView , BookSlotView

router = DefaultRouter()

router.register('invoices', InvoiceViewSet, basename='invoice')

from django.contrib import admin

urlpatterns = [
    path('pin/verify/', VerifyPinView.as_view()),
    path('my-invoices/', MyInvoicesView.as_view()),
    path('availableslots/', AvailableSlotsView.as_view()),
    path('bookslot/', BookSlotView.as_view()), 
] + router.urls  