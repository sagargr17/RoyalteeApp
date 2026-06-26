from django.contrib import admin
from django.urls import path

urlpatterns = [
    path('admin/', admin.site.urls),  # this becomes admin.yourapp.com/admin
]