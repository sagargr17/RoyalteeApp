# tenants/middleware.py
from django.db import connection
from django_tenants.utils import get_tenant_model, get_public_schema_name
from django.http import JsonResponse



class HeaderTenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        
        print(request)
        tenant_id = request.headers.get('X-Tenant-ID')
        
        tenant_id = 'edric'

        if not tenant_id:
            return JsonResponse({'error': 'X-Tenant-ID header required'}, status=400)
        TenantModel = get_tenant_model()
        try:
            tenant = TenantModel.objects.get(schema_name=tenant_id)
        except TenantModel.DoesNotExist:
            return JsonResponse({'error': 'Invalid tenant'}, status=404)

        connection.set_tenant(tenant)  # 🔑 this switches the Postgres schema
        request.tenant = tenant    

        response = self.get_response(request)
        connection.set_schema_to_public() 
        return response
    
    

