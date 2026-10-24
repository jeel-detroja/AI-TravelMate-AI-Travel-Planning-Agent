from django.contrib import admin

from .models import Itinerary, Trip


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ("destination", "user", "start_date", "duration_days", "status", "created_at")
    list_filter = ("status", "currency", "travel_style")
    search_fields = ("destination", "user__username")
    readonly_fields = ("created_at", "updated_at")


@admin.register(Itinerary)
class ItineraryAdmin(admin.ModelAdmin):
    list_display = ("trip", "generator", "status", "estimated_total_cost", "generated_at")
    readonly_fields = ("generated_at",)
