# tenants/middleware.py
from django.http import JsonResponse
from django_tenants.utils import get_tenant_model


class HeaderTenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # TenantMainMiddleware already resolved tenant via subdomain
        # skip entirely — no header needed
        if hasattr(request, 'tenant'):
            return self.get_response(request)

        # fallback: try header (only for direct IP/API access)
        tenant_id = request.headers.get('X-Tenant-ID')
        if not tenant_id:
            # no subdomain match AND no header — pass through
            # let Django handle it (will 404 or hit public urls)
            return self.get_response(request)

        TenantModel = get_tenant_model()
        
        try:
            from django.db import connection
            print(tenant_id)
            tenant = TenantModel.objects.get(schema_name=tenant_id)
            connection.set_tenant(tenant)
            request.tenant = tenant
        except TenantModel.DoesNotExist:
            return JsonResponse({'error': 'Invalid tenant'}, status=404)

        return self.get_response(request)