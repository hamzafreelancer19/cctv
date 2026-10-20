from rest_framework.exceptions import PermissionDenied


class TenantQuerysetMixin:
    """Scope queryset to organizations the user belongs to."""

    organization_field = "organization"

    def get_user_organizations(self):
        user = self.request.user
        if not user or not user.is_authenticated:
            return []
        from apps.tenancy.models import UserMembership

        return list(UserMembership.objects.filter(user=user).values_list("organization_id", flat=True))

    def get_queryset(self):
        qs = super().get_queryset()
        org_ids = self.get_user_organizations()
        if not org_ids:
            return qs.none()
        return qs.filter(**{f"{self.organization_field}__in": org_ids})


def get_membership(user, organization):
    from apps.tenancy.models import UserMembership

    try:
        return UserMembership.objects.get(user=user, organization=organization)
    except UserMembership.DoesNotExist:
        return None


def require_role(user, organization, allowed_roles):
    membership = get_membership(user, organization)
    if membership is None or membership.role not in allowed_roles:
        raise PermissionDenied("Insufficient permissions for this organization.")
    return membership
