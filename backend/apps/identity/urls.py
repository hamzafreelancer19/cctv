from django.urls import path

from .views import (
    AttendanceListView,
    AttendanceReportView,
    ConsentListCreateView,
    FaceEnrollView,
    FaceMatchView,
    GalleryExportView,
    PersonDetailView,
    PersonListCreateView,
    PersonSightingDetailView,
    PersonSightingListView,
    UnknownSightingListView,
    UnknownSightingReviewView,
    VisitorActionView,
    VisitorListCreateView,
)

urlpatterns = [
    path("persons/", PersonListCreateView.as_view(), name="person-list"),
    path("persons/<uuid:pk>/", PersonDetailView.as_view(), name="person-detail"),
    path("persons/enroll/", FaceEnrollView.as_view(), name="person-enroll"),
    path("persons/sightings/", PersonSightingListView.as_view(), name="person-sighting-list"),
    path(
        "persons/sightings/<uuid:pk>/",
        PersonSightingDetailView.as_view(),
        name="person-sighting-detail",
    ),
    path("consents/", ConsentListCreateView.as_view(), name="consent-list"),
    path("face/gallery/", GalleryExportView.as_view(), name="face-gallery"),
    path("face/match/", FaceMatchView.as_view(), name="face-match"),
    path("attendance/", AttendanceListView.as_view(), name="attendance-list"),
    path("attendance/report/", AttendanceReportView.as_view(), name="attendance-report"),
    path("visitors/", VisitorListCreateView.as_view(), name="visitor-list"),
    path("visitors/<uuid:pk>/<str:action>/", VisitorActionView.as_view(), name="visitor-action"),
    path("unknown-sightings/", UnknownSightingListView.as_view(), name="unknown-list"),
    path("unknown-sightings/<uuid:pk>/review/", UnknownSightingReviewView.as_view(), name="unknown-review"),
]
