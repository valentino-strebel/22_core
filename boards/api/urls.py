"""
URL configuration for board endpoints.

Endpoints:
    - GET  /api/boards/              → List all boards the user has access to
    - POST /api/boards/              → Create a new board
    - GET  /api/boards/{board_id}/   → Retrieve details of a board
    - PATCH /api/boards/{board_id}/  → Update board title and members
    - DELETE /api/boards/{board_id}/ → Delete a board
"""

from django.urls import path
from .views import BoardListCreateView, BoardDetailUpdateDestroyView

#: URL patterns for board operations
urlpatterns = [
    path(
        "boards/",
        BoardListCreateView.as_view(),
        name="board-list-create",
    ),
    path(
        "boards/<int:board_id>/",
        BoardDetailUpdateDestroyView.as_view(),
        name="board-detail-update-destroy",
    ),
]
