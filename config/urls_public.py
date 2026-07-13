from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from django.contrib import admin
# from .views import UserProfileView # Your DRF View



print("hitttinggg... public")

urlpatterns = [
    path('admin/', admin.site.urls),  # this becomes admin.yourapp.com/admin    
    path('api/', include('billing.urls')),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


