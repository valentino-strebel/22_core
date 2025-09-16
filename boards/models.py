from django.conf import settings
from django.db import models


class Board(models.Model):
    """
    Represents a project board that groups tasks and members.

    Attributes:
        title (CharField): Name of the board.
        owner (ForeignKey[User]): User who owns the board. Deleting the owner deletes the board.
        members (ManyToManyField[User]): Additional users who are members of the board.

    Example:
        board = Board.objects.create(title="Development Roadmap", owner=user1)
        board.members.add(user2, user3)

    __str__:
        Returns a string in the form "Board(<id>) - <title>".
    """
    title = models.CharField(max_length=255)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_boards",
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="boards",
        blank=True,
    )

    def __str__(self):
        return f"Board({self.id}) - {self.title}"
