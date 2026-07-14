# tenants/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Client, Domain



class CreateTenantView(APIView):
    def post(self, request):
        name = request.data['company_name']
        schema_name = request.data['schema_name']  # e.g. "acme"

        tenant = Client.objects.create(
            schema_name=schema_name,
            name=name,
        )
        Domain.objects.create(
            domain=f"{schema_name}.yourapp.com",
            tenant=tenant,
            is_primary=True
        )
        # schema + migrations run automatically because auto_create_schema=True

        return Response({'tenant_id': schema_name}, status=201)