from rest_framework import generics, permissions, status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from django.conf import settings
from django.db import connection
from django.utils import timezone

from apps.cameras.authentication import EdgeAPIKeyAuthentication, EdgeServiceUser
from apps.cameras.models import Camera
from apps.common.permissions import TenantQuerysetMixin, require_role
from apps.events.models import DetectionEvent
from apps.tenancy.models import Role

from .models import (
    NotificationDeliveryLog,
    NotificationJob,
    PasswordPolicy,
    RecordingJob,
    SessionPolicy,
    SIEMForwardJob,
    SnapshotObject,
    SSOProvider,
)
from .serializers import (
    NotificationDeliveryLogSerializer,
    NotificationJobSerializer,
    PasswordPolicySerializer,
    RecordingJobSerializer,
    SessionPolicySerializer,
    SIEMForwardJobSerializer,
    SnapshotObjectSerializer,
    SSOProviderSerializer,
)
from .services import refresh_signed_url, register_snapshot, store_and_register_upload


class NotificationJobListView(TenantQuerysetMixin, generics.ListAPIView):
    serializer_class = NotificationJobSerializer
    permission_classes = [permissions.IsAuthenticated]
    organization_field = "organization"
    filterset_fields = ("status", "channel")

    def get_queryset(self):
        return NotificationJob.objects.filter(organization_id__in=self.get_user_organizations())


class NotificationDeliveryLogListView(TenantQuerysetMixin, generics.ListAPIView):
    serializer_class = NotificationDeliveryLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return NotificationDeliveryLog.objects.filter(
            job__organization_id__in=self.get_user_organizations()
        ).select_related("job")


class RecordingJobListView(TenantQuerysetMixin, generics.ListAPIView):
    serializer_class = RecordingJobSerializer
    permission_classes = [permissions.IsAuthenticated]
    organization_field = "organization"
    filterset_fields = ("status", "vendor", "camera")

    def get_queryset(self):
        return RecordingJob.objects.filter(organization_id__in=self.get_user_organizations()).select_related(
            "camera"
        )


class SnapshotListView(TenantQuerysetMixin, generics.ListAPIView):
    serializer_class = SnapshotObjectSerializer
    permission_classes = [permissions.IsAuthenticated]
    organization_field = "organization"
    filterset_fields = ("camera",)

    def get_queryset(self):
        return SnapshotObject.objects.filter(organization_id__in=self.get_user_organizations()).select_related(
            "camera"
        )


class SnapshotDetailView(TenantQuerysetMixin, generics.RetrieveAPIView):
    serializer_class = SnapshotObjectSerializer
    permission_classes = [permissions.IsAuthenticated]
    organization_field = "organization"

    def get_queryset(self):
        return SnapshotObject.objects.filter(organization_id__in=self.get_user_organizations())

    def retrieve(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.storage_backend in {"s3", "minio"} or request.query_params.get("resign") == "1":
            try:
                refresh_signed_url(obj)
            except Exception:
                pass
        return Response(self.get_serializer(obj).data)


class SnapshotUploadView(APIView):
    """Edge uploads snapshot file/metadata → evidence storage + signed URL."""

    authentication_classes = [EdgeAPIKeyAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request):
        camera_id = request.data.get("camera_id")
        event_id = request.data.get("event_id")
        camera = Camera.objects.select_related("site__organization").filter(id=camera_id, is_active=True).first()
        if not camera:
            return Response({"error": {"code": "NOT_FOUND", "message": "Camera not found."}}, status=404)
        if isinstance(request.user, EdgeServiceUser) and request.user.device:
            if camera.site_id != request.user.device.site_id:
                return Response({"error": {"code": "FORBIDDEN", "message": "Camera not on edge site."}}, status=403)

        event = None
        if event_id:
            event = DetectionEvent.objects.filter(id=event_id, camera=camera).first()

        upload = request.FILES.get("file")
        if upload:
            obj = store_and_register_upload(
                organization=camera.site.organization,
                camera=camera,
                file_obj=upload,
                event=event,
                content_type=upload.content_type or "image/jpeg",
                uploaded_by_edge=True,
            )
            return Response(SnapshotObjectSerializer(obj).data, status=status.HTTP_201_CREATED)

        snapshot_key = request.data.get("snapshot_key") or ""
        if not snapshot_key:
            return Response(
                {"error": {"code": "BAD_REQUEST", "message": "file or snapshot_key required."}},
                status=400,
            )
        obj = register_snapshot(
            organization=camera.site.organization,
            camera=camera,
            snapshot_key=snapshot_key,
            snapshot_url=request.data.get("snapshot_url", ""),
            thumbnail_url=request.data.get("thumbnail_url", ""),
            event=event,
            content_type=request.data.get("content_type") or "image/jpeg",
            mime_type=request.data.get("mime_type") or "",
            checksum=request.data.get("checksum") or "",
            width=int(request.data["width"]) if request.data.get("width") else None,
            height=int(request.data["height"]) if request.data.get("height") else None,
            size_bytes=int(request.data.get("size_bytes") or 0),
            uploaded_by_edge=True,
            storage_backend=request.data.get("storage_backend") or "local",
        )
        return Response(SnapshotObjectSerializer(obj).data, status=status.HTTP_201_CREATED)


class SSOProviderListCreateView(TenantQuerysetMixin, generics.ListCreateAPIView):
    serializer_class = SSOProviderSerializer
    permission_classes = [permissions.IsAuthenticated]
    organization_field = "organization"

    def get_queryset(self):
        return SSOProvider.objects.filter(organization_id__in=self.get_user_organizations())

    def perform_create(self, serializer):
        from apps.tenancy.models import Organization

        org_id = self.request.data.get("organization") or self.get_user_organizations()[0]
        org = Organization.objects.get(id=org_id)
        require_role(self.request.user, org, [Role.OWNER, Role.ADMIN])
        serializer.save(organization=org)


class PasswordPolicyView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from apps.tenancy.models import Organization

        org_id = request.query_params.get("organization") or request.user.memberships.values_list(
            "organization_id", flat=True
        ).first()
        org = Organization.objects.get(id=org_id)
        policy, _ = PasswordPolicy.objects.get_or_create(organization=org)
        return Response(PasswordPolicySerializer(policy).data)

    def put(self, request):
        from apps.tenancy.models import Organization

        org_id = request.data.get("organization") or request.user.memberships.values_list(
            "organization_id", flat=True
        ).first()
        org = Organization.objects.get(id=org_id)
        require_role(request.user, org, [Role.OWNER, Role.ADMIN])
        policy, _ = PasswordPolicy.objects.get_or_create(organization=org)
        ser = PasswordPolicySerializer(policy, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data)


class SessionPolicyView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from apps.tenancy.models import Organization

        org_id = request.query_params.get("organization") or request.user.memberships.values_list(
            "organization_id", flat=True
        ).first()
        org = Organization.objects.get(id=org_id)
        policy, _ = SessionPolicy.objects.get_or_create(organization=org)
        return Response(SessionPolicySerializer(policy).data)

    def put(self, request):
        from apps.tenancy.models import Organization

        org_id = request.data.get("organization") or request.user.memberships.values_list(
            "organization_id", flat=True
        ).first()
        org = Organization.objects.get(id=org_id)
        require_role(request.user, org, [Role.OWNER, Role.ADMIN])
        policy, _ = SessionPolicy.objects.get_or_create(organization=org)
        ser = SessionPolicySerializer(policy, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data)


class SIEMJobListView(TenantQuerysetMixin, generics.ListAPIView):
    serializer_class = SIEMForwardJobSerializer
    permission_classes = [permissions.IsAuthenticated]
    organization_field = "organization"
    filterset_fields = ("status", "target")

    def get_queryset(self):
        return SIEMForwardJob.objects.filter(organization_id__in=self.get_user_organizations())


class MetricsView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        if not settings.PROMETHEUS_ENABLED:
            return Response({"error": "metrics disabled"}, status=404)
        from apps.ops.observability import render_metrics

        body, content_type = render_metrics()
        from django.http import HttpResponse

        return HttpResponse(body, content_type=content_type)


class ReadyView(APIView):
    """Kubernetes readiness: DB reachable."""

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        try:
            connection.ensure_connection()
            return Response({"status": "ready", "timestamp": timezone.now().isoformat()})
        except Exception as exc:
            return Response({"status": "not_ready", "error": str(exc)}, status=503)


class LiveView(APIView):
    """Kubernetes liveness probe."""

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response({"status": "alive", "timestamp": timezone.now().isoformat()})
