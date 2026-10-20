import threading

from django.conf import settings
from django.db import models

from apps.common.models import TimestampedModel, UUIDModel
from apps.tenancy.models import Organization

_audit_context = threading.local()


def set_audit_context(user=None, organization=None, ip_address=None):
    _audit_context.user = user
    _audit_context.organization = organization
    _audit_context.ip_address = ip_address


def get_audit_context():
    return {
        "user": getattr(_audit_context, "user", None),
        "organization": getattr(_audit_context, "organization", None),
        "ip_address": getattr(_audit_context, "ip_address", None),
    }


class AuditLog(UUIDModel, TimestampedModel):
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="audit_logs", null=True, blank=True
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_logs"
    )
    action = models.CharField(max_length=64)
    resource_type = models.CharField(max_length=64)
    resource_id = models.CharField(max_length=64, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    details = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["organization", "-created_at"])]

    def __str__(self):
        return f"{self.action} {self.resource_type} by {self.actor}"


def _resolve_actor(actor):
    """Return a real User (or None); AnonymousUser cannot be assigned to AuditLog.actor."""
    if actor is None:
        return None
    if getattr(actor, "is_authenticated", False) is False:
        return None
    return actor


def log_audit(action, resource_type, resource_id="", organization=None, actor=None, details=None, ip_address=None):
    ctx = get_audit_context()
    AuditLog.objects.create(
        organization=organization or ctx.get("organization"),
        actor=_resolve_actor(actor if actor is not None else ctx.get("user")),
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id),
        ip_address=ip_address or ctx.get("ip_address"),
        details=details or {},
    )
