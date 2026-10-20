from django.urls import path

from .views import MembershipMeView, OrganizationListView

urlpatterns = [
    path("organizations/", OrganizationListView.as_view(), name="organization-list"),
    path("memberships/me/", MembershipMeView.as_view(), name="membership-me"),
]
