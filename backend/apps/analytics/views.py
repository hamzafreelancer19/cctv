from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.permissions import TenantQuerysetMixin, require_role
from apps.sites.models import Zone
from apps.tenancy.models import Role

from .models import AnalyticsRule, CrowdStatistic, LoiterEvent, ObjectEvent, RiskIncident
from .serializers import (
    AnalyticsRuleSerializer,
    CrowdStatisticSerializer,
    LoiterEventSerializer,
    ObjectEventSerializer,
    RiskIncidentSerializer,
    ZoneAnalyticsSerializer,
)
from .services import crowd_summary


class ZoneAnalyticsListCreateView(TenantQuerysetMixin, generics.ListCreateAPIView):
    serializer_class = ZoneAnalyticsSerializer
    permission_classes = [permissions.IsAuthenticated]
    organization_field = "site__organization"
    filterset_fields = ("site", "is_restricted", "is_active", "priority")
    search_fields = ("name",)

    def get_queryset(self):
        return Zone.objects.filter(site__organization_id__in=self.get_user_organizations()).select_related("site")

    def perform_create(self, serializer):
        org = serializer.validated_data["site"].organization
        require_role(self.request.user, org, [Role.OWNER, Role.ADMIN])
        serializer.save()


class ZoneAnalyticsDetailView(TenantQuerysetMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ZoneAnalyticsSerializer
    permission_classes = [permissions.IsAuthenticated]
    organization_field = "site__organization"

    def get_queryset(self):
        return Zone.objects.filter(site__organization_id__in=self.get_user_organizations()).select_related("site")

    def perform_update(self, serializer):
        require_role(self.request.user, serializer.instance.organization, [Role.OWNER, Role.ADMIN])
        serializer.save()

    def perform_destroy(self, instance):
        require_role(self.request.user, instance.organization, [Role.OWNER, Role.ADMIN])
        instance.delete()


class LoiterEventListView(TenantQuerysetMixin, generics.ListAPIView):
    serializer_class = LoiterEventSerializer
    permission_classes = [permissions.IsAuthenticated]
    organization_field = "organization"
    filterset_fields = ("camera", "zone", "severity")

    def get_queryset(self):
        return LoiterEvent.objects.filter(organization_id__in=self.get_user_organizations()).select_related(
            "camera", "zone"
        )


class CrowdListView(TenantQuerysetMixin, generics.ListAPIView):
    serializer_class = CrowdStatisticSerializer
    permission_classes = [permissions.IsAuthenticated]
    organization_field = "organization"
    filterset_fields = ("camera", "zone")

    def get_queryset(self):
        return CrowdStatistic.objects.filter(organization_id__in=self.get_user_organizations()).select_related(
            "camera", "zone"
        )


class CrowdSummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user_orgs = list(request.user.memberships.values_list("organization_id", flat=True))
        org_id = request.query_params.get("organization") or (str(user_orgs[0]) if user_orgs else None)
        camera_id = request.query_params.get("camera")
        if not org_id:
            return Response({"error": {"code": "BAD_REQUEST", "message": "organization required."}}, status=400)
        allowed = {str(o) for o in user_orgs}
        if str(org_id) not in allowed:
            return Response({"error": {"code": "FORBIDDEN", "message": "Organization access denied."}}, status=403)
        return Response(crowd_summary(org_id, camera_id=camera_id))


class ObjectEventListView(TenantQuerysetMixin, generics.ListAPIView):
    serializer_class = ObjectEventSerializer
    permission_classes = [permissions.IsAuthenticated]
    organization_field = "organization"
    filterset_fields = ("camera", "zone", "kind")

    def get_queryset(self):
        return ObjectEvent.objects.filter(organization_id__in=self.get_user_organizations()).select_related(
            "camera", "zone"
        )


class RiskIncidentListView(TenantQuerysetMixin, generics.ListAPIView):
    serializer_class = RiskIncidentSerializer
    permission_classes = [permissions.IsAuthenticated]
    organization_field = "organization"
    filterset_fields = ("risk_level", "status", "camera", "site")

    def get_queryset(self):
        return RiskIncident.objects.filter(organization_id__in=self.get_user_organizations()).select_related(
            "camera", "site", "zone", "rule"
        )


class RiskIncidentActionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk, action):
        incident = RiskIncident.objects.filter(
            id=pk, organization_id__in=request.user.memberships.values_list("organization_id", flat=True)
        ).first()
        if not incident:
            return Response({"error": {"code": "NOT_FOUND", "message": "Incident not found."}}, status=404)
        require_role(request.user, incident.organization, [Role.OWNER, Role.ADMIN, Role.OPERATOR])
        now = timezone.now()
        if action == "acknowledge":
            incident.status = "acknowledged"
            incident.acknowledged_by = request.user
            incident.acknowledged_at = now
        elif action == "resolve":
            incident.status = "resolved"
            incident.resolved_at = now
        elif action == "false_positive":
            incident.status = "false_positive"
            incident.resolved_at = now
        else:
            return Response({"error": {"code": "BAD_REQUEST", "message": "Unknown action."}}, status=400)
        incident.save()
        return Response(RiskIncidentSerializer(incident).data)


class AnalyticsRuleListCreateView(TenantQuerysetMixin, generics.ListCreateAPIView):
    serializer_class = AnalyticsRuleSerializer
    permission_classes = [permissions.IsAuthenticated]
    organization_field = "organization"
    filterset_fields = ("is_active", "site", "zone", "risk_level")

    def get_queryset(self):
        return AnalyticsRule.objects.filter(organization_id__in=self.get_user_organizations()).prefetch_related(
            "actions"
        )

    def perform_create(self, serializer):
        org = serializer.validated_data["organization"]
        require_role(self.request.user, org, [Role.OWNER, Role.ADMIN])
        serializer.save()


class AnalyticsRuleDetailView(TenantQuerysetMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AnalyticsRuleSerializer
    permission_classes = [permissions.IsAuthenticated]
    organization_field = "organization"

    def get_queryset(self):
        return AnalyticsRule.objects.filter(organization_id__in=self.get_user_organizations()).prefetch_related(
            "actions"
        )

    def perform_update(self, serializer):
        require_role(self.request.user, serializer.instance.organization, [Role.OWNER, Role.ADMIN])
        serializer.save()

    def perform_destroy(self, instance):
        require_role(self.request.user, instance.organization, [Role.OWNER, Role.ADMIN])
        instance.delete()


class IncidentTimelineView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        org_ids = list(request.user.memberships.values_list("organization_id", flat=True))
        incidents = RiskIncident.objects.filter(organization_id__in=org_ids).order_by("-created_at")[:50]
        loiters = LoiterEvent.objects.filter(organization_id__in=org_ids).order_by("-created_at")[:30]
        objects = ObjectEvent.objects.filter(organization_id__in=org_ids).order_by("-created_at")[:30]
        timeline = []
        for i in incidents:
            timeline.append(
                {
                    "kind": "incident",
                    "id": str(i.id),
                    "title": i.title,
                    "severity": i.risk_level,
                    "created_at": i.created_at.isoformat(),
                }
            )
        for l in loiters:
            timeline.append(
                {
                    "kind": "loiter",
                    "id": str(l.id),
                    "title": f"Loitering {l.dwell_seconds:.0f}s",
                    "severity": l.severity,
                    "created_at": l.created_at.isoformat(),
                }
            )
        for o in objects:
            timeline.append(
                {
                    "kind": "object",
                    "id": str(o.id),
                    "title": f"{o.kind}: {o.object_class}",
                    "severity": o.severity,
                    "created_at": o.created_at.isoformat(),
                }
            )
        timeline.sort(key=lambda x: x["created_at"], reverse=True)
        return Response({"results": timeline[:80]})
