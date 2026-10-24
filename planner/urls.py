from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("how-it-works/", views.how_it_works, name="how_it_works"),
    path("privacy/", views.privacy, name="privacy"),
    path("health/", views.health, name="health"),
    path("trips/new/", views.create_trip, name="create_trip"),
    path("trips/", views.saved_trips, name="saved_trips"),
    path("trips/<int:pk>/", views.trip_detail, name="trip_detail"),
    path("trips/<int:pk>/regenerate/", views.regenerate_trip, name="regenerate_trip"),
    path("trips/<int:pk>/delete/", views.delete_trip, name="delete_trip"),
]
