# # config/urls_tenants.py
# from django.contrib import admin
# from django.urls import path, include

# urlpatterns = [
#     path('admin/', admin.site.urls),
#     path('api/', include('billing.urls')),  
# ]


from django.contrib import admin
from django.urls import path

urlpatterns = [
    path('admin/', admin.site.urls),  
]