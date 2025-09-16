from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("authentication.api.urls")),
    path("api/", include("boards.api.urls")),
    path("api/", include("tasks.api.urls")),
    path("api-auth/", include("rest_framework.urls")),

]
