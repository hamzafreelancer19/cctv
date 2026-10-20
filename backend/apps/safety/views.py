from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.permissions import TenantQuerysetMixin, require_role
from apps.tenancy.models import Role

from .models import (
    EmergencyIncident,
    FallEvent,
    FireEvent,
    PPEEvent,
    SafetyProfile,
    SmokeEvent,
    WeaponEvent,
)
from .serializers import (
    EmergencyIncidentSerializer,
    FallEventSerializer,
    FireEventSerializer,
    PPEEventSerializer,
    SafetyProfileSerializer,
    SmokeEventSerializer,
    WeaponEventSerializer,
)


class BaseSafetyEventList(TenantQuerysetMixin, generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    organization_field = "organization"
    filterset_fields = ("camera", "zone")
    ordering = ["-created_at"]

    def get_queryset(self):
        return self.model.objects.filter(
            organization_id__in=self.get_user_organizations()
        ).select_related("camera", "camera__site", "zone")


class FireEventListView(BaseSafetyEventList):
    model = FireEvent
    serializer_class = FireEventSerializer
    filterset_fields = BaseSafetyEventList.filterset_fields + ("verified", "environment")


class SmokeEventListView(BaseSafetyEventList):
    model = SmokeEvent
    serializer_class = SmokeEventSerializer
    filterset_fields = BaseSafetyEventList.filterset_fields + ("density_level", "persistent")


class WeaponEventListView(BaseSafetyEventList):
    model = WeaponEvent
    serializer_class = WeaponEventSerializer
    filterset_fields = BaseSafetyEventList.filterset_fields + ("weapon_type", "associated")


class FallEventListView(BaseSafetyEventList):
    model = FallEvent
    serializer_class = FallEventSerializer
    filterset_fields = BaseSafetyEventList.filterset_fields + ("status",)


class PPEEventListView(BaseSafetyEventList):
    model = PPEEvent
    serializer_class = PPEEventSerializer
    filterset_fields = BaseSafetyEventList.filterset_fields + ("compliant", "person_type")


class SafetyProfileListCreateView(TenantQuerysetMixin, generics.ListCreateAPIView):
    serializer_class = SafetyProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    organization_field = "camera__site__organization"

    def get_queryset(self):
        return SafetyProfile.objects.filter(
            camera__site__organization_id__in=self.get_user_organizations()
        ).select_related("camera")

    def perform_create(self, serializer):
        organization = serializer.validated_data["camera"].site.organization
        require_role(self.request.user, organization, [Role.OWNER, Role.ADMIN])
        serializer.save()


class SafetyProfileDetailView(TenantQuerysetMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SafetyProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    organization_field = "camera__site__organization"

    def get_queryset(self):
        return SafetyProfile.objects.filter(
            camera__site__organization_id__in=self.get_user_organizations()
        )

    def perform_update(self, serializer):
        require_role(
            self.request.user,
            serializer.instance.camera.site.organization,
            [Role.OWNER, Role.ADMIN],
        )
        serializer.save()


class EmergencyIncidentListView(TenantQuerysetMixin, generics.ListAPIView):
    serializer_class = EmergencyIncidentSerializer
    permission_classes = [permissions.IsAuthenticated]
    organization_field = "organization"
    filterset_fields = ("severity", "status", "site", "camera")

    def get_queryset(self):
        return (
            EmergencyIncident.objects.filter(organization_id__in=self.get_user_organizations())
            .select_related("site", "camera", "zone")
            .prefetch_related("actions", "escalations", "event_links")
        )


class EmergencyIncidentActionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk, action):
        incident = EmergencyIncident.objects.filter(
            id=pk,
            organization_id__in=request.user.memberships.values_list("organization_id", flat=True),
        ).first()
        if not incident:
            return Response({"error": {"code": "NOT_FOUND", "message": "Incident not found."}}, status=404)
        require_role(request.user, incident.organization, [Role.OWNER, Role.ADMIN, Role.OPERATOR])
        now = timezone.now()
        if action == "acknowledge":
            incident.status = "acknowledged"
            incident.acknowledged_by = request.user
            incident.acknowledged_at = now
        elif action in {"contain", "contained"}:
            incident.status = "contained"
        elif action == "resolve":
            incident.status = "resolved"
            incident.resolved_at = now
        elif action == "false_positive":
            incident.status = "false_positive"
            incident.resolved_at = now
        else:
            return Response({"error": {"code": "BAD_ACTION", "message": "Unsupported action."}}, status=400)
        incident.save()
        return Response(EmergencyIncidentSerializer(incident).data)


class SafetySummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        org_ids = request.user.memberships.values_list("organization_id", flat=True)
        today = timezone.now().date()
        incidents = EmergencyIncident.objects.filter(organization_id__in=org_ids)
        ppe = PPEEvent.objects.filter(organization_id__in=org_ids, created_at__date=today)
        total_ppe = ppe.count()
        return Response(
            {
                "fire_today": FireEvent.objects.filter(
                    organization_id__in=org_ids, created_at__date=today
                ).count(),
                "smoke_today": SmokeEvent.objects.filter(
                    organization_id__in=org_ids, created_at__date=today
                ).count(),
                "weapon_today": WeaponEvent.objects.filter(
                    organization_id__in=org_ids, created_at__date=today
                ).count(),
                "falls_open": FallEvent.objects.filter(
                    organization_id__in=org_ids, status__in=["fallen", "immobile"]
                ).count(),
                "ppe_compliance_percent": round(
                    100 * ppe.filter(compliant=True).count() / total_ppe, 1
                )
                if total_ppe
                else 100.0,
                "incidents_open": incidents.filter(status__in=["open", "acknowledged"]).count(),
                "incidents_emergency": incidents.filter(
                    status__in=["open", "acknowledged"], severity="emergency"
                ).count(),
            }
        )
