from rest_framework import generics, permissions, status
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response

from boards.models import Board
from tasks.models import Task, Comment
from .serializers import (
    TaskCreateSerializer,
    TaskDetailSerializer,
    TaskUpdateSerializer,
    TaskReviewingSerializer,
    CommentSerializer,
)


class TaskCreateView(generics.CreateAPIView):
    """
    POST /api/tasks/
    Create a new task on a board.

    Permissions:
        - Authenticated user only.
        - User must be the board owner or a board member.

    Request body:
        {
          "board": int,
          "title": str,
          "description": str,
          "status": str,
          "priority": str,
          "assignee_id": int|null,
          "reviewer_id": int|null,
          "due_date": "YYYY-MM-DD"
        }

    Responses:
        201 Created → Task object with assignee/reviewer details and comments_count.
        403 Forbidden → User not member of the board.
        404 Not Found → Board does not exist.
    """
    queryset = Task.objects.all()
    serializer_class = TaskCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        board_id = request.data.get("board")
        if board_id in (None, ""):
            return super().create(request, *args, **kwargs)
        try:
            board = Board.objects.get(pk=board_id)
        except Board.DoesNotExist:
            raise NotFound("Board not found.")
        user = self.request.user
        if not (board.owner_id == user.id or board.members.filter(id=user.id).exists()):
            raise PermissionDenied("You must be a member of this board to create a task.")
        return super().create(request, *args, **kwargs)


class TaskDetailUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET /api/tasks/{task_id}/
    Retrieve task details including assignee, reviewer, and comments_count.

    PATCH /api/tasks/{task_id}/
    Partially update a task. The board cannot be changed.

    DELETE /api/tasks/{task_id}/
    Delete a task (authorization rules may be enforced if `created_by` is used).

    Permissions:
        - Authenticated user only.
        - User must be the board owner or a board member.

    Responses:
        200 OK → Task object.
        403 Forbidden → User not member of the board.
        404 Not Found → Task not found.
    """
    queryset = Task.objects.select_related("board", "board__owner", "assignee", "reviewer")
    permission_classes = [permissions.IsAuthenticated]
    lookup_url_kwarg = "task_id"
    lookup_field = "pk"

    def get_serializer_class(self):
        if self.request.method.upper() == "PATCH":
            return TaskUpdateSerializer
        return TaskDetailSerializer

    def get_object(self):
        try:
            task = self.get_queryset().get(pk=self.kwargs.get(self.lookup_url_kwarg))
        except Task.DoesNotExist:
            raise NotFound("Task not found.")

        user = self.request.user
        board = task.board
        if not (board.owner_id == user.id or board.members.filter(id=user.id).exists()):
            raise PermissionDenied("You must be a member of this board to access this task.")

        return task

    def update(self, request, *args, **kwargs):
        if "board" in request.data:
            raise ValidationError({"board": "Changing the board is not allowed."})
        kwargs["partial"] = True
        return super().update(request, *args, **kwargs)


class CommentListCreateView(generics.ListCreateAPIView):
    """
    GET /api/tasks/{task_id}/comments/
    List comments on a task in chronological order.

    POST /api/tasks/{task_id}/comments/
    Create a new comment on a task.

    Permissions:
        - Authenticated user only.
        - User must be the board owner or a board member.

    Responses:
        200 OK → List of comments.
        201 Created → Created comment object.
        403 Forbidden → User not member of the board.
        404 Not Found → Task not found.
    """
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_url_kwarg = "task_id"

    def get_task(self):
        task_id = self.kwargs.get(self.lookup_url_kwarg)
        try:
            return Task.objects.select_related("board", "board__owner").get(pk=task_id)
        except Task.DoesNotExist:
            raise NotFound("Task not found.")

    def _enforce_membership(self, task):
        board = task.board
        user = self.request.user
        if not (board.owner_id == user.id or board.members.filter(id=user.id).exists()):
            raise PermissionDenied("You must be a member of the board to access comments for this task.")

    def get_queryset(self):
        task = self.get_task()
        self._enforce_membership(task)
        return Comment.objects.filter(task=task).select_related("author")

    def perform_create(self, serializer):
        task = self.get_task()
        self._enforce_membership(task)
        serializer.save(task=task, author=self.request.user)


class CommentDetailDestroyView(generics.RetrieveDestroyAPIView):
    """
    GET /api/tasks/{task_id}/comments/{comment_id}/
    Retrieve a single comment on a task.

    DELETE /api/tasks/{task_id}/comments/{comment_id}/
    Delete a comment.

    Permissions:
        - Authenticated user only.
        - User must be the board owner or a board member.

    Responses:
        200 OK → Comment object.
        403 Forbidden → User not member of the board.
        404 Not Found → Task or comment not found.
    """
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_url_kwarg = "comment_id"
    lookup_field = "pk"

    def _get_task_or_404(self):
        task_id = self.kwargs.get("task_id")
        try:
            return Task.objects.select_related("board", "board__owner").get(pk=task_id)
        except Task.DoesNotExist:
            raise NotFound("Task not found.")

    def get_queryset(self):
        task = self._get_task_or_404()
        return Comment.objects.filter(task=task).select_related("author", "task", "task__board")

    def get_object(self):
        try:
            comment = self.get_queryset().get(pk=self.kwargs.get(self.lookup_url_kwarg))
        except Comment.DoesNotExist:
            raise NotFound("Comment not found.")
        return comment


class TaskReviewingListView(generics.ListAPIView):
    """
    GET /api/tasks/reviewing/
    List tasks where the current user is the reviewer.

    Permissions:
        - Authenticated user only.

    Responses:
        200 OK → List of tasks assigned to the current user as reviewer.
    """
    serializer_class = TaskReviewingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return (
            Task.objects.filter(reviewer=user)
            .select_related("board", "assignee", "reviewer")
            .order_by("id")
        )


class TaskAssignedToMeListView(generics.ListAPIView):
    """
    GET /api/tasks/assigned-to-me/
    List tasks where the current user is the assignee.

    Permissions:
        - Authenticated user only.

    Responses:
        200 OK → List of tasks assigned to the current user.
    """
    serializer_class = TaskReviewingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return (
            Task.objects.filter(assignee=user)
            .select_related("board", "assignee", "reviewer")
            .order_by("id")
        )
