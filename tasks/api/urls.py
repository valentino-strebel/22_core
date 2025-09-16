"""
URL configuration for task management endpoints.

This module defines the REST API routes for task and comment operations.
Each route maps to a corresponding class-based view in `.views`.

Endpoints:
    - POST   /tasks/                         → Create a new task
    - GET    /tasks/<task_id>/               → Retrieve task details
    - PATCH  /tasks/<task_id>/               → Update a task
    - DELETE /tasks/<task_id>/               → Delete a task
    - GET    /tasks/reviewing/               → List tasks where current user is reviewer
    - GET    /tasks/assigned-to-me/          → List tasks assigned to current user
    - GET    /tasks/<task_id>/comments/      → List comments on a task
    - POST   /tasks/<task_id>/comments/      → Create a new comment on a task
    - GET    /tasks/<task_id>/comments/<comment_id>/ → Retrieve a comment
    - DELETE /tasks/<task_id>/comments/<comment_id>/ → Delete a comment
"""

from django.urls import path
from .views import (
    TaskCreateView,
    TaskDetailUpdateDestroyView,
    TaskReviewingListView,
    TaskAssignedToMeListView,
    CommentListCreateView,
    CommentDetailDestroyView,
)

urlpatterns = [
    path(
        "tasks/",
        TaskCreateView.as_view(),
        name="task-create",
    ),
    path(
        "tasks/<int:task_id>/",
        TaskDetailUpdateDestroyView.as_view(),
        name="task-detail-update-destroy",
    ),
    path(
        "tasks/reviewing/",
        TaskReviewingListView.as_view(),
        name="task-reviewing",
    ),
    path(
        "tasks/assigned-to-me/",
        TaskAssignedToMeListView.as_view(),
        name="task-assigned-to-me",
    ),
    path(
        "tasks/<int:task_id>/comments/",
        CommentListCreateView.as_view(),
        name="task-comments",
    ),
    path(
        "tasks/<int:task_id>/comments/<int:comment_id>/",
        CommentDetailDestroyView.as_view(),
        name="task-comment-detail-destroy",
    ),
]
