from django.conf import settings
from django.db import models
from boards.models import Board


class Task(models.Model):
    """
    Represents a task belonging to a board.

    Attributes:
        board (ForeignKey[Board]): Board this task belongs to.
        title (CharField): Short title of the task.
        description (TextField): Optional longer description.
        status (CharField): Current state of the task.
            Choices: "to-do", "in-progress", "review", "done".
        priority (CharField): Priority level of the task.
            Choices: "low", "medium", "high".
        assignee (ForeignKey[User]): User assigned to complete the task.
        reviewer (ForeignKey[User]): User assigned to review the task.
        due_date (DateField): Optional due date for task completion.
        created_by (ForeignKey[User]): User who created the task.

    Example:
        Task.objects.create(
            board=board,
            title="Write documentation",
            description="Add docstrings to all serializers",
            status=Task.STATUS_TO_DO,
            priority=Task.PRIORITY_MEDIUM,
            assignee=user1,
            reviewer=user2,
            due_date="2025-09-20",
            created_by=user1,
        )
    """

    STATUS_TO_DO = "to-do"
    STATUS_IN_PROGRESS = "in-progress"
    STATUS_REVIEW = "review"
    STATUS_DONE = "done"
    STATUS_CHOICES = [
        (STATUS_TO_DO, "to-do"),
        (STATUS_IN_PROGRESS, "in-progress"),
        (STATUS_REVIEW, "review"),
        (STATUS_DONE, "done"),
    ]

    PRIORITY_LOW = "low"
    PRIORITY_MEDIUM = "medium"
    PRIORITY_HIGH = "high"
    PRIORITY_CHOICES = [
        (PRIORITY_LOW, "low"),
        (PRIORITY_MEDIUM, "medium"),
        (PRIORITY_HIGH, "high"),
    ]

    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name="tasks")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES)
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_tasks",
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="review_tasks",
    )
    due_date = models.DateField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_tasks",
    )

    def __str__(self):
        return f"Task({self.id}) - {self.title}"


class Comment(models.Model):
    """
    Represents a comment on a task.

    Attributes:
        task (ForeignKey[Task]): The task this comment belongs to.
        author (ForeignKey[User]): The user who wrote the comment.
        content (TextField): Body text of the comment.
        created_at (DateTimeField): Timestamp of creation.

    Meta:
        ordering = ["created_at", "id"]  # Sorted chronologically with ID as tiebreaker.

    Example:
        Comment.objects.create(
            task=task,
            author=user,
            content="Looks good, but add more examples.",
        )
    """
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]

    def __str__(self):
        return f"Comment({self.id}) on Task({self.task_id})"
