from rest_framework import generics, permissions
from rest_framework.response import Response

from apps.common.permissions import TenantQuerysetMixin

from .models import Organization, UserMembership
from .serializers import MembershipMeSerializer, OrganizationSerializer


class OrganizationListView(TenantQuerysetMixin, generics.ListAPIView):
    serializer_class = OrganizationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        org_ids = self.get_user_organizations()
        return Organization.objects.filter(id__in=org_ids, is_active=True)


class MembershipMeView(generics.ListAPIView):
    serializer_class = MembershipMeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserMembership.objects.filter(user=self.request.user).select_related("organization")

    def list(self, request, *args, **kwargs):
        memberships = self.get_queryset()
        data = [
            {"organization": OrganizationSerializer(m.organization).data, "role": m.role}
            for m in memberships
        ]
        return Response(data)
