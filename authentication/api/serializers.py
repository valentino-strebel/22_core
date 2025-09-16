from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model

User = get_user_model()


class RegistrationSerializer(serializers.Serializer):
    """
    Serializer for registering a new user.

    Fields:
        fullname (str): The full name of the user.
        email (str): User's email address (must be unique).
        password (str): User's password (min length: 8).
        repeated_password (str): Confirmation of the password.

    Methods:
        validate_email: Ensures the email is not already taken.
        validate: Ensures password and repeated_password match.
        create: Creates a new user with validated data.
    """
    fullname = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    repeated_password = serializers.CharField(write_only=True, min_length=8)

    def validate_email(self, value):
        """
        Check if a user with the provided email already exists.
        """
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate(self, attrs):
        """
        Ensure that password and repeated_password are identical.
        """
        if attrs["password"] != attrs["repeated_password"]:
            raise serializers.ValidationError({"repeated_password": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        """
        Create and return a new user instance.

        Args:
            validated_data (dict): Validated user data.

        Returns:
            User: A newly created User instance.
        """
        validated_data.pop("repeated_password")
        full_name = validated_data.pop("fullname")
        return User.objects.create_user(full_name=full_name, **validated_data)


class LoginSerializer(serializers.Serializer):
    """
    Serializer for logging in a user.

    Fields:
        email (str): User's email address.
        password (str): User's password.

    Methods:
        validate: Authenticates the user with the provided credentials.
    """
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        """
        Authenticate user with email and password.

        Raises:
            serializers.ValidationError: If authentication fails.

        Returns:
            dict: Attributes with authenticated 'user' added.
        """
        email = attrs.get("email")
        password = attrs.get("password")

        if email and password:
            user = authenticate(request=self.context.get("request"), email=email, password=password)
            if not user:
                raise serializers.ValidationError("Invalid email or password.", code="authorization")
        else:
            raise serializers.ValidationError("Must include 'email' and 'password'.", code="authorization")

        attrs["user"] = user
        return attrs


class EmailCheckQuerySerializer(serializers.Serializer):
    """
    Serializer for validating an email query parameter.

    Fields:
        email (str): The email address to check.
    """
    email = serializers.EmailField(required=True)
