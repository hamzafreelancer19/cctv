from rest_framework import generics, permissions

from apps.common.permissions import TenantQuerysetMixin

from .models import AuditLog
from .serializers import AuditLogSerializer


class AuditLogListView(TenantQuerysetMixin, generics.ListAPIView):
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    organization_field = "organization"
    filterset_fields = ("action", "resource_type")
    ordering = ["-created_at"]

    def get_queryset(self):
        return AuditLog.objects.filter(organization_id__in=self.get_user_organizations()).select_related("actor")
