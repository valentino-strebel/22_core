from django.db.models import Q, Count, Prefetch
from rest_framework import generics, permissions, status
from rest_framework.exceptions import PermissionDenied, NotFound
from rest_framework.response import Response

from boards.models import Board
from .serializers import (
    BoardCreateSerializer,
    BoardDetailSerializer,
    BoardMembersUpdateSerializer,
)
from tasks.models import Task



class BoardListCreateView(generics.ListCreateAPIView):
    """
    GET /api/boards/
    List boards the authenticated user owns or is a member of.

    POST /api/boards/
    Create a new board. The authenticated user becomes the owner.

    Permissions:
        - Authenticated user only.

    Responses:
        200 OK → List of boards with counts.
        201 Created → Created board object.
    """
    serializer_class = BoardCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return (
            Board.objects.filter(Q(owner=user) | Q(members=user))
            .distinct()
            .annotate(
                ticket_count=Count("tasks", distinct=True),
                tasks_to_do_count=Count(
                    "tasks", filter=Q(tasks__status=Task.STATUS_TO_DO), distinct=True
                ),
                tasks_high_prio_count=Count(
                    "tasks", filter=Q(tasks__priority=Task.PRIORITY_HIGH), distinct=True
                ),
            )
            .order_by("id")
        )

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class BoardDetailUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET /api/boards/{board_id}/
    Retrieve board details including members and tasks.

    PATCH /api/boards/{board_id}/
    Update the board title and replace the members list.

    DELETE /api/boards/{board_id}/
    Delete the board. Only the owner may perform this action.

    Permissions:
        - Authenticated user only.
        - GET/PATCH → Owner or member.
        - DELETE → Owner only.

    Responses:
        200 OK → Board details.
        204 No Content → Board deleted.
        403 Forbidden → User not authorized.
        404 Not Found → Board not found.
    """
    permission_classes = [permissions.IsAuthenticated]
    lookup_url_kwarg = "board_id"
    lookup_field = "pk"

    def get_queryset(self):
        return (
            Board.objects.all()
            .select_related("owner")
            .prefetch_related(
                "members",
                Prefetch(
                    "tasks",
                    queryset=Task.objects.select_related("assignee", "reviewer").order_by("id"),
                ),
            )
        )

    def _get_board_or_404(self):
        try:
            return self.get_queryset().get(pk=self.kwargs.get(self.lookup_url_kwarg))
        except Board.DoesNotExist:
            raise NotFound("Board not found.")

    def get_object(self):
        board = self._get_board_or_404()
        user = self.request.user
        if self.request.method.upper() in ("GET", "PATCH"):
            if board.owner_id != user.id and not board.members.filter(id=user.id).exists():
                raise PermissionDenied("You do not have access to this board.")
        return board

    def get_serializer_class(self):
        if self.request.method.upper() == "PATCH":
            return BoardMembersUpdateSerializer
        return BoardDetailSerializer

    def update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        board = self._get_board_or_404()
        if request.user.id != board.owner_id:
            raise PermissionDenied("Only the board owner may delete this board.")
        board.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
