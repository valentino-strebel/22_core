"""
Serializers for task management endpoints.

Defines DRF serializers for creating, reading, updating, and reviewing `Task`
objects, as well as creating and listing `Comment` objects. Includes the
utility `_user_to_brief` to normalize user-like inputs into a compact dict.
"""

from django.contrib.auth import get_user_model
from rest_framework import serializers

from boards.models import Board
from tasks.models import Task, Comment


def _user_to_brief(user):
    """
    Normalize a user-like object or dict into a compact representation.

    Accepts:
        - Django User-like instance (id, email, full name fields).
        - dict payload (e.g. {"user_id": 123, "email": "a@b.com", "fullname": "Ada"}).

    Returns:
        dict | None: {"id": int|None, "email": str, "fullname": str} or None.
    """
    if not user:
        return None

    if isinstance(user, dict):
        uid = user.get("id", user.get("user_id"))
        email = user.get("email") or ""
        fullname = (user.get("fullname") or "").strip()
        if not fullname:
            first = (user.get("first_name") or "").strip()
            last = (user.get("last_name") or "").strip()
            fullname = (f"{first} {last}").strip() or (user.get("username") or "").strip()
        return {"id": uid, "email": email, "fullname": fullname or ""}

    uid = getattr(user, "id", None) or getattr(user, "pk", None) or getattr(user, "user_id", None)
    email = getattr(user, "email", "") or ""

    fullname = ""
    get_full_name = getattr(user, "get_full_name", None)
    if callable(get_full_name):
        fullname = (get_full_name() or "").strip()
    if not fullname:
        first = getattr(user, "first_name", "") or ""
        last = getattr(user, "last_name", "") or ""
        fullname = (f"{first} {last}").strip()
    if not fullname:
        fullname = (
            getattr(user, "full_name", "")
            or getattr(user, "fullname", "")
            or getattr(user, "username", "")
        ).strip()

    return {"id": uid, "email": email, "fullname": fullname or ""}


class TaskCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a task.

    Write-only:
        assignee_id (int|null)
        reviewer_id (int|null)

    Read-only:
        assignee (dict)
        reviewer (dict)
        comments_count (int)
    """
    assignee_id = serializers.IntegerField(required=False, allow_null=True, write_only=True)
    reviewer_id = serializers.IntegerField(required=False, allow_null=True, write_only=True)

    assignee = serializers.SerializerMethodField(read_only=True)
    reviewer = serializers.SerializerMethodField(read_only=True)
    comments_count = serializers.SerializerMethodField(read_only=True)

    board = serializers.PrimaryKeyRelatedField(queryset=Board.objects.all())

    class Meta:
        model = Task
        fields = (
            "id",
            "board",
            "title",
            "description",
            "status",
            "priority",
            "assignee_id",
            "reviewer_id",
            "assignee",
            "reviewer",
            "due_date",
            "comments_count",
        )
        read_only_fields = ("id", "assignee", "reviewer", "comments_count")

    def validate(self, attrs):
        """
        Ensure assignee/reviewer IDs are valid users and members of the board.
        """
        board = attrs.get("board")
        User = get_user_model()

        assignee_id = attrs.pop("assignee_id", None)
        reviewer_id = attrs.pop("reviewer_id", None)

        if assignee_id is not None:
            try:
                assignee = User.objects.get(pk=assignee_id)
            except User.DoesNotExist:
                raise serializers.ValidationError({"assignee_id": "User not found."})
            if not (assignee.id == board.owner_id or board.members.filter(id=assignee.id).exists()):
                raise serializers.ValidationError({"assignee_id": "User is not a member of this board."})
            attrs["assignee"] = assignee

        if reviewer_id is not None:
            try:
                reviewer = User.objects.get(pk=reviewer_id)
            except User.DoesNotExist:
                raise serializers.ValidationError({"reviewer_id": "User not found."})
            if not (reviewer.id == board.owner_id or board.members.filter(id=reviewer.id).exists()):
                raise serializers.ValidationError({"reviewer_id": "User is not a member of this board."})
            attrs["reviewer"] = reviewer

        return attrs

    def get_assignee(self, obj):
        return _user_to_brief(obj.assignee)

    def get_reviewer(self, obj):
        return _user_to_brief(obj.reviewer)

    def get_comments_count(self, obj):
        return obj.comments.count()


class TaskDetailSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for detailed task view.
    """
    assignee = serializers.SerializerMethodField(read_only=True)
    reviewer = serializers.SerializerMethodField(read_only=True)
    comments_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Task
        fields = (
            "id",
            "title",
            "description",
            "status",
            "priority",
            "assignee",
            "reviewer",
            "due_date",
            "comments_count",
        )
        read_only_fields = fields

    def get_assignee(self, obj):
        return _user_to_brief(obj.assignee)

    def get_reviewer(self, obj):
        return _user_to_brief(obj.reviewer)

    def get_comments_count(self, obj):
        return obj.comments.count()


class TaskUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for partially updating a task.

    Write-only:
        assignee_id (int | "" | false | null)
        reviewer_id (int | "" | false | null)

    Read-only:
        assignee (dict)
        reviewer (dict)
    """
    assignee_id = serializers.IntegerField(required=False, allow_null=True, write_only=True)
    reviewer_id = serializers.IntegerField(required=False, allow_null=True, write_only=True)

    assignee = serializers.SerializerMethodField(read_only=True)
    reviewer = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Task
        fields = (
            "id",
            "title",
            "description",
            "status",
            "priority",
            "assignee_id",
            "reviewer_id",
            "assignee",
            "reviewer",
            "due_date",
        )
        read_only_fields = ("id", "assignee", "reviewer")

    def validate(self, attrs):
        """
        Ensure updated assignee/reviewer IDs are valid and members of the board.
        """
        task: Task = self.instance
        board = task.board
        User = get_user_model()

        assignee_id = attrs.pop("assignee_id", None)
        reviewer_id = attrs.pop("reviewer_id", None)

        if assignee_id is not None:
            if assignee_id in ("", False):
                attrs["assignee"] = None
            else:
                try:
                    assignee = User.objects.get(pk=assignee_id)
                except User.DoesNotExist:
                    raise serializers.ValidationError({"assignee_id": "User not found."})
                if not (assignee.id == board.owner_id or board.members.filter(id=assignee.id).exists()):
                    raise serializers.ValidationError({"assignee_id": "User is not a member of this board."})
                attrs["assignee"] = assignee

        if reviewer_id is not None:
            if reviewer_id in ("", False):
                attrs["reviewer"] = None
            else:
                try:
                    reviewer = User.objects.get(pk=reviewer_id)
                except User.DoesNotExist:
                    raise serializers.ValidationError({"reviewer_id": "User not found."})
                if not (reviewer.id == board.owner_id or board.members.filter(id=reviewer.id).exists()):
                    raise serializers.ValidationError({"reviewer_id": "User is not a member of this board."})
                attrs["reviewer"] = reviewer

        return attrs

    def get_assignee(self, obj):
        return _user_to_brief(obj.assignee)

    def get_reviewer(self, obj):
        return _user_to_brief(obj.reviewer)


class CommentSerializer(serializers.ModelSerializer):
    """
    Serializer for listing and creating comments on tasks.
    """
    author = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Comment
        fields = ("id", "created_at", "author", "content")
        read_only_fields = ("id", "created_at", "author")

    def validate_content(self, value: str):
        """
        Ensure content is not empty or whitespace-only.
        """
        if not value or not value.strip():
            raise serializers.ValidationError("Content cannot be empty.")
        return value

    def get_author(self, obj):
        user = obj.author
        if not user:
            return ""
        return _user_to_brief(user)["fullname"]


class TaskReviewingSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for tasks assigned to the current user as reviewer.
    """
    board = serializers.IntegerField(source="board_id", read_only=True)
    assignee = serializers.SerializerMethodField(read_only=True)
    reviewer = serializers.SerializerMethodField(read_only=True)
    comments_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Task
        fields = (
            "id",
            "board",
            "title",
            "description",
            "status",
            "priority",
            "assignee",
            "reviewer",
            "due_date",
            "comments_count",
        )
        read_only_fields = fields

    def get_assignee(self, obj):
        return _user_to_brief(obj.assignee)

    def get_reviewer(self, obj):
        return _user_to_brief(obj.reviewer)

    def get_comments_count(self, obj):
        return obj.comments.count()
