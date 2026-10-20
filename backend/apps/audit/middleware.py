from django.utils.deprecation import MiddlewareMixin

from .models import set_audit_context


class AuditContextMiddleware(MiddlewareMixin):
    def process_request(self, request):
        ip = request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip() or request.META.get("REMOTE_ADDR")
        org = None
        if hasattr(request, "user") and request.user.is_authenticated:
            membership = request.user.memberships.select_related("organization").first()
            org = membership.organization if membership else None
        set_audit_context(user=getattr(request, "user", None), organization=org, ip_address=ip)
