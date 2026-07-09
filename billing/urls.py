# billing/urls.py
from rest_framework.routers import DefaultRouter
from .views import InvoiceViewSet

from django.urls import path
from .views import VerifyPinView, MyInvoicesView

router = DefaultRouter()
router.register('invoices', InvoiceViewSet, basename='invoice')

from django.contrib import admin

admin.site.site_header = "Administration Panel"

urlpatterns = [
    path('pin/verify/', VerifyPinView.as_view()),
    path('my-invoices/', MyInvoicesView.as_view()),
    
    
] + router.urls


urlpatterns = router.urls
