from django.urls import path

from .views import DetectionEventListView, EventIngestView, EventReviewView

urlpatterns = [
    path("events/", DetectionEventListView.as_view(), name="event-list"),
    path("events/ingest/", EventIngestView.as_view(), name="event-ingest"),
    path("events/<uuid:pk>/review/", EventReviewView.as_view(), name="event-review"),
]
