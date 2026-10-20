from django.urls import path

from .views import AlertAcknowledgeView, AlertListView, AlertRuleListCreateView

urlpatterns = [
    path("alert-rules/", AlertRuleListCreateView.as_view(), name="alert-rule-list"),
    path("alerts/", AlertListView.as_view(), name="alert-list"),
    path("alerts/<uuid:pk>/acknowledge/", AlertAcknowledgeView.as_view(), name="alert-acknowledge"),
]
