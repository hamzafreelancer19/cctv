from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone

from apps.cameras.authentication import EdgeAPIKeyAuthentication, EdgeServiceUser
from apps.cameras.models import Camera
from apps.common.permissions import TenantQuerysetMixin, require_role
from apps.tenancy.models import Role

from .models import DetectionEvent, ReviewStatus
from .pipeline import IngestValidationError, ingest_from_edge_payload
from .serializers import DetectionEventSerializer, EventIngestSerializer, EventReviewSerializer


class HealthView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response({"status": "healthy", "service": "sentinelvision-api", "timestamp": timezone.now().isoformat()})


class DashboardSummaryView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        org_ids = list(request.user.memberships.values_list("organization_id", flat=True))
        today = timezone.now().date()
        cameras = Camera.objects.filter(site__organization_id__in=org_ids, is_active=True)
        events = DetectionEvent.objects.filter(camera__site__organization_id__in=org_ids)
        from apps.alerts.models import Alert
        from apps.cameras.models import EdgeDevice

        alerts = Alert.objects.filter(organization_id__in=org_ids)
        edges = EdgeDevice.objects.filter(site__organization_id__in=org_ids, is_active=True)

        return Response(
            {
                "cameras_total": cameras.count(),
                "cameras_online": cameras.filter(status="online").count(),
                "events_today": events.filter(created_at__date=today).count(),
                "events_pending_review": events.filter(review_status=ReviewStatus.PENDING).count(),
                "alerts_open": alerts.filter(status="open").count(),
                "alerts_critical": alerts.filter(status="open", severity="critical").count(),
                "edge_devices_online": edges.filter(status="online").count(),
                "edge_devices_total": edges.count(),
            }
        )


class DetectionEventListView(TenantQuerysetMixin, generics.ListAPIView):
    serializer_class = DetectionEventSerializer
    permission_classes = [permissions.IsAuthenticated]
    organization_field = "camera__site__organization"
    filterset_fields = ("camera", "event_type", "severity", "review_status")
    ordering_fields = ("created_at", "confidence", "severity")
    ordering = ["-created_at"]
    search_fields = ("camera__name", "edge_event_id")

    def get_queryset(self):
        return DetectionEvent.objects.filter(
            camera__site__organization_id__in=self.get_user_organizations()
        ).select_related("camera", "camera__site", "zone", "edge_device")

    def delete(self, request):
        queryset = self.get_queryset()
        organizations = {event.organization for event in queryset}
        for organization in organizations:
            require_role(request.user, organization, [Role.OWNER, Role.ADMIN])

        deleted_count = queryset.count()
        queryset.delete()
        return Response({"deleted": deleted_count}, status=status.HTTP_200_OK)


class EventIngestView(APIView):
    """
    Idempotent edge ingest.

    Lookup(edge_device_id, edge_event_id) → 200 if exists, else insert → 201.
    """

    authentication_classes = [EdgeAPIKeyAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = EventIngestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        edge_device = None
        if isinstance(request.user, EdgeServiceUser) and request.user.device:
            edge_device = request.user.device

        try:
            result = ingest_from_edge_payload(data, edge_device=edge_device)
        except IngestValidationError as exc:
            return Response(
                {"error": {"code": exc.code, "message": exc.message}},
                status=exc.status_code,
            )

        body = DetectionEventSerializer(result.event).data
        return Response(
            body,
            status=status.HTTP_201_CREATED if result.created else status.HTTP_200_OK,
        )


class EventReviewView(TenantQuerysetMixin, generics.UpdateAPIView):
    serializer_class = EventReviewSerializer
    permission_classes = [permissions.IsAuthenticated]
    organization_field = "camera__site__organization"
    http_method_names = ["get", "patch"]

    def get_queryset(self):
        return DetectionEvent.objects.filter(camera__site__organization_id__in=self.get_user_organizations())

    def perform_update(self, serializer):
        event = self.get_object()
        require_role(self.request.user, event.organization, [Role.OWNER, Role.ADMIN, Role.OPERATOR])
        serializer.save(reviewed_by=self.request.user, reviewed_at=timezone.now())
