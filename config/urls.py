from django.contrib import admin
from django.urls import include, path

from planner import views as planner_views

handler404 = "planner.views.handler404"
handler500 = "planner.views.handler500"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/signup/", planner_views.signup, name="signup"),
    path("accounts/", include("django.contrib.auth.urls")),
    path("", include("planner.urls")),
]
