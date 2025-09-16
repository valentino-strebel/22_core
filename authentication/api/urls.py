from django.urls import path
from .views import RegistrationView, LoginView, EmailCheckView

# URL patterns for authentication-related API endpoints.
# Each endpoint maps to a corresponding APIView in views.py.
urlpatterns = [
    # User registration endpoint
    # POST -> Register a new user and return a token + user details
    path("registration/", RegistrationView.as_view(), name="api-registration"),

    # User login endpoint
    # POST -> Authenticate user and return a token + user details
    path("login/", LoginView.as_view(), name="api-login"),

    # Email check endpoint
    # GET -> Check if an email exists (requires authentication)
    path("email-check/", EmailCheckView.as_view(), name="api-email-check"),
]
