"""Invitations app URL configuration."""

from django.urls import path

from invitations.views import (
    InvitationApproveView,
    InvitationDetailView,
    InvitationListCreateView,
    InvitationRejectView,
)

app_name = "invitations"

urlpatterns = [
    path(
        "<int:pk>/approve/", InvitationApproveView.as_view(), name="invitation-approve"
    ),
    path("<int:pk>/reject/", InvitationRejectView.as_view(), name="invitation-reject"),
    path("<int:pk>/", InvitationDetailView.as_view(), name="invitation-detail"),
    path("", InvitationListCreateView.as_view(), name="invitation-list"),
]
