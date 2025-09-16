from django.contrib.auth import get_user_model
from rest_framework import serializers

from boards.models import Board
from tasks.models import Task


def _user_to_brief(user):
    """
    Normalize a user-like object or dict into a compact representation.

    Accepts:
        - Django User-like model instance (id, email, get_full_name, etc.)
        - dict payload such as {"token": "...", "fullname": "...", "email": "...", "user_id": 123}

    Returns:
        dict: {"id": int|None, "email": str, "fullname": str} or None.
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
            composed = (f"{first} {last}").strip()
            fullname = composed or (user.get("username") or "").strip()
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


class BoardCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new board or listing boards.

    Write-only:
        members (list[int]): IDs of users to set as board members.

    Read-only:
        member_count (int): Number of board members.
        ticket_count (int): Total number of tasks on the board.
        tasks_to_do_count (int): Number of tasks with status "to-do".
        tasks_high_prio_count (int): Number of tasks with high priority.
        owner_id (int): ID of the board owner.
    """
    members = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        allow_empty=True,
        write_only=True,
    )
    member_count = serializers.SerializerMethodField(read_only=True)
    ticket_count = serializers.SerializerMethodField(read_only=True)
    tasks_to_do_count = serializers.SerializerMethodField(read_only=True)
    tasks_high_prio_count = serializers.SerializerMethodField(read_only=True)
    owner_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Board
        fields = (
            "id",
            "title",
            "members",
            "member_count",
            "ticket_count",
            "tasks_to_do_count",
            "tasks_high_prio_count",
            "owner_id",
        )
        read_only_fields = (
            "id",
            "member_count",
            "ticket_count",
            "tasks_to_do_count",
            "tasks_high_prio_count",
            "owner_id",
        )

    def validate_members(self, value):
        user_model = get_user_model()
        unique_ids = list(dict.fromkeys(value))
        existing = set(user_model.objects.filter(id__in=unique_ids).values_list("id", flat=True))
        missing = [uid for uid in unique_ids if uid not in existing]
        if missing:
            raise serializers.ValidationError(f"Unknown user IDs: {missing}")
        return unique_ids

    def create(self, validated_data):
        member_ids = validated_data.pop("members", [])
        owner = validated_data.pop("owner", None)
        if owner is None and "request" in self.context:
            owner = self.context["request"].user

        board = Board.objects.create(owner=owner, **validated_data)
        if member_ids:
            user_model = get_user_model()
            board.members.set(user_model.objects.filter(id__in=member_ids))
        return board

    def get_member_count(self, obj):
        return obj.members.count()

    def get_ticket_count(self, obj):
        annotated = getattr(obj, "ticket_count", None)
        if annotated is not None:
            return int(annotated)
        return obj.tasks.count()

    def get_tasks_to_do_count(self, obj):
        annotated = getattr(obj, "tasks_to_do_count", None)
        if annotated is not None:
            return int(annotated)
        return obj.tasks.filter(status=Task.STATUS_TO_DO).count()

    def get_tasks_high_prio_count(self, obj):
        annotated = getattr(obj, "tasks_high_prio_count", None)
        if annotated is not None:
            return int(annotated)
        return obj.tasks.filter(priority=Task.PRIORITY_HIGH).count()


class TaskNestedSerializer(serializers.ModelSerializer):
    """
    Nested serializer for representing tasks inside a board detail.

    Fields:
        id (int)
        title (str)
        description (str)
        status (str)
        priority (str)
        assignee (dict): Normalized user brief.
        reviewer (dict): Normalized user brief.
        due_date (date)
        comments_count (int)
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

    def get_assignee(self, obj):
        return _user_to_brief(obj.assignee)

    def get_reviewer(self, obj):
        return _user_to_brief(obj.reviewer)

    def get_comments_count(self, obj):
        return obj.comments.count()


class BoardDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for retrieving detailed information about a board.

    Read-only:
        owner_id (int): ID of the board owner.
        members (list[dict]): List of normalized user briefs.
        tasks (list[TaskNestedSerializer]): All tasks on the board.
    """
    owner_id = serializers.IntegerField(read_only=True)
    members = serializers.SerializerMethodField(read_only=True)
    tasks = TaskNestedSerializer(many=True, read_only=True)

    class Meta:
        model = Board
        fields = ("id", "title", "owner_id", "members", "tasks")

    def get_members(self, obj):
        return [_user_to_brief(u) for u in obj.members.all()]


class BoardMembersUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating a board's title and member list.

    Write-only:
        members (list[int]): IDs of users to set as members.

    Read-only:
        owner_data (dict): Normalized brief of the board owner.
        members_data (list[dict]): Normalized briefs of the board members.
    """
    members = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        allow_empty=True,
        write_only=True,
    )
    owner_data = serializers.SerializerMethodField(read_only=True)
    members_data = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Board
        fields = ("id", "title", "members", "owner_data", "members_data")
        read_only_fields = ("id", "owner_data", "members_data")

    def validate_members(self, value):
        user_model = get_user_model()
        unique_ids = list(dict.fromkeys(value))
        existing = set(user_model.objects.filter(id__in=unique_ids).values_list("id", flat=True))
        missing = [uid for uid in unique_ids if uid not in existing]
        if missing:
            raise serializers.ValidationError(f"Unknown user IDs: {missing}")
        return unique_ids

    def update(self, instance, validated_data):
        title = validated_data.get("title", None)
        if title is not None:
            instance.title = title
            instance.save(update_fields=["title"])

        if "members" in validated_data:
            member_ids = validated_data["members"]
            user_model = get_user_model()
            users = user_model.objects.filter(id__in=member_ids)
            instance.members.set(users)

        return instance

    def get_owner_data(self, obj):
        return _user_to_brief(obj.owner)

    def get_members_data(self, obj):
        return [_user_to_brief(u) for u in obj.members.all()]
