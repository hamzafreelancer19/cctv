from rest_framework import generics, permissions

from apps.common.permissions import TenantQuerysetMixin, require_role
from apps.tenancy.models import Role

from .models import Site, Zone
from .serializers import SiteSerializer, ZoneSerializer


class SiteListCreateView(TenantQuerysetMixin, generics.ListCreateAPIView):
    serializer_class = SiteSerializer
    permission_classes = [permissions.IsAuthenticated]
    organization_field = "organization"
    search_fields = ("name", "address")
    ordering_fields = ("name", "created_at")

    def get_queryset(self):
        return Site.objects.filter(organization_id__in=self.get_user_organizations()).select_related("organization")

    def perform_create(self, serializer):
        org = serializer.validated_data["organization"]
        require_role(self.request.user, org, [Role.OWNER, Role.ADMIN])
        serializer.save()


class SiteDetailView(TenantQuerysetMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SiteSerializer
    permission_classes = [permissions.IsAuthenticated]
    organization_field = "organization"

    def get_queryset(self):
        return Site.objects.filter(organization_id__in=self.get_user_organizations())

    def perform_update(self, serializer):
        require_role(self.request.user, serializer.instance.organization, [Role.OWNER, Role.ADMIN])
        serializer.save()

    def perform_destroy(self, instance):
        require_role(self.request.user, instance.organization, [Role.OWNER, Role.ADMIN])
        instance.delete()


class ZoneListCreateView(TenantQuerysetMixin, generics.ListCreateAPIView):
    serializer_class = ZoneSerializer
    permission_classes = [permissions.IsAuthenticated]
    organization_field = "site__organization"
    filterset_fields = ("site", "is_restricted", "is_active")

    def get_queryset(self):
        return Zone.objects.filter(site__organization_id__in=self.get_user_organizations()).select_related("site")

    def perform_create(self, serializer):
        site = serializer.validated_data["site"]
        require_role(self.request.user, site.organization, [Role.OWNER, Role.ADMIN])
        serializer.save()


class ZoneDetailView(TenantQuerysetMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ZoneSerializer
    permission_classes = [permissions.IsAuthenticated]
    organization_field = "site__organization"

    def get_queryset(self):
        return Zone.objects.filter(site__organization_id__in=self.get_user_organizations()).select_related("site")

    def perform_update(self, serializer):
        require_role(self.request.user, serializer.instance.site.organization, [Role.OWNER, Role.ADMIN])
        zone = serializer.save()
        # Any update is treated as config drift for edge zone hydration.
        Zone.objects.filter(pk=zone.pk).update(config_version=zone.config_version + 1)
        zone.refresh_from_db(fields=["config_version"])

    def perform_destroy(self, instance):
        require_role(self.request.user, instance.site.organization, [Role.OWNER, Role.ADMIN])
        instance.delete()
