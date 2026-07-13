from django.contrib import admin
from django.urls import path, include
# from billing.views import verify_page


print("Hitting....")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('billing.urls')),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('api/token/', __import__('rest_framework_simplejwt.views', fromlist=['TokenObtainPairView']).TokenObtainPairView.as_view()),
    path('api/token/refresh/', __import__('rest_framework_simplejwt.views', fromlist=['TokenRefreshView']).TokenRefreshView.as_view()),
    # path('verify/', verify_page),               
]