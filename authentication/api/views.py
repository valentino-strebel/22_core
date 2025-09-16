from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model

from .serializers import RegistrationSerializer
from .serializers import LoginSerializer
from .serializers import EmailCheckQuerySerializer

User = get_user_model()


class RegistrationView(APIView):
    """
    API endpoint for user registration.

    Permissions:
        - AllowAny: Accessible to unauthenticated users.

    Methods:
        post:
            Registers a new user with the provided data, creates a token,
            and returns user information along with the token.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """
        Handle POST request to register a new user.

        Request body:
            {
                "fullname": str,
                "email": str,
                "password": str,
                "repeated_password": str
            }

        Responses:
            201 Created:
                {
                    "token": str,
                    "fullname": str,
                    "email": str,
                    "user_id": int
                }
            400 Bad Request: If validation fails.
        """
        serializer = RegistrationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)

        return Response(
            {
                "token": token.key,
                "fullname": user.full_name,
                "email": user.email,
                "user_id": user.pk,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """
    API endpoint for user login.

    Permissions:
        - AllowAny: Accessible to unauthenticated users.

    Methods:
        post:
            Authenticates the user and returns a token along with user details.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """
        Handle POST request to authenticate a user.

        Request body:
            {
                "email": str,
                "password": str
            }

        Responses:
            200 OK:
                {
                    "token": str,
                    "fullname": str,
                    "email": str,
                    "user_id": int
                }
            400 Bad Request: If credentials are invalid.
        """
        serializer = LoginSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.validated_data["user"]
        token, _ = Token.objects.get_or_create(user=user)

        return Response(
            {
                "token": token.key,
                "fullname": user.full_name,
                "email": user.email,
                "user_id": user.pk,
            },
            status=status.HTTP_200_OK,
        )


class EmailCheckView(APIView):
    """
    API endpoint to check if an email exists in the system.

    Permissions:
        - IsAuthenticated: Only accessible to logged-in users.

    Methods:
        get:
            Accepts an email as a query parameter and returns the user details if found.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """
        Handle GET request to check if an email exists.

        Query parameters:
            email (str): The email to check.

        Responses:
            200 OK:
                {
                    "id": int,
                    "email": str,
                    "fullname": str
                }
            400 Bad Request: If email parameter is invalid.
            404 Not Found: If no user exists with the given email.
        """
        q = EmailCheckQuerySerializer(data=request.query_params)
        if not q.is_valid():
            return Response(q.errors, status=status.HTTP_400_BAD_REQUEST)

        email = q.validated_data["email"]
        user = User.objects.filter(email__iexact=email).only("id", "email", "full_name").first()
        if not user:
            return Response({"detail": "Email not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response(
            {
                "id": user.id,
                "email": user.email,
                "fullname": user.full_name,
            },
            status=status.HTTP_200_OK,
        )
