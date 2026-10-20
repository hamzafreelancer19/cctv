from django.urls import path

from .views import SiteDetailView, SiteListCreateView, ZoneDetailView, ZoneListCreateView

urlpatterns = [
    path("sites/", SiteListCreateView.as_view(), name="site-list"),
    path("sites/<uuid:pk>/", SiteDetailView.as_view(), name="site-detail"),
    path("zones/", ZoneListCreateView.as_view(), name="zone-list"),
    path("zones/<uuid:pk>/", ZoneDetailView.as_view(), name="zone-detail"),
]
