from rest_framework import serializers

from .models import Site, Zone


class SiteSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source="organization.name", read_only=True)

    class Meta:
        model = Site
        fields = (
            "id",
            "organization",
            "organization_name",
            "name",
            "address",
            "timezone",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class ZoneSerializer(serializers.ModelSerializer):
    site_name = serializers.CharField(source="site.name", read_only=True)
    organization = serializers.UUIDField(source="site.organization_id", read_only=True)
    camera_ids = serializers.SerializerMethodField()

    class Meta:
        model = Zone
        fields = (
            "id",
            "site",
            "site_name",
            "organization",
            "name",
            "polygon_json",
            "is_restricted",
            "is_active",
            "priority",
            "loitering_seconds",
            "visitor_loitering_seconds",
            "ignore_employees",
            "max_occupancy",
            "access_start",
            "access_end",
            "after_hours_restricted",
            "entry_line_json",
            "camera_ids",
            "config_version",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "config_version", "created_at", "updated_at")

    def get_camera_ids(self, obj):
        return [str(c.id) for c in obj.linked_cameras.all()]
