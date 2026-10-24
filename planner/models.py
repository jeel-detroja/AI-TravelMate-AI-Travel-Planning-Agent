from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse

from .constants import (
    COMPANIONS,
    CURRENCIES,
    MAX_DURATION_DAYS,
    MAX_TRAVELLERS,
    PACES,
    TRAVEL_STYLES,
)


class Trip(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        GENERATING = "generating", "Generating"
        READY = "ready", "Ready"
        FAILED = "failed", "Failed"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="trips"
    )
    destination = models.CharField(max_length=160)
    resolved_name = models.CharField(max_length=255, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    start_date = models.DateField()
    duration_days = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(MAX_DURATION_DAYS)]
    )
    budget = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    currency = models.CharField(max_length=3, choices=CURRENCIES, default="INR")
    travellers = models.PositiveSmallIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(MAX_TRAVELLERS)],
    )
    interests = models.JSONField(default=list)
    travel_style = models.CharField(max_length=12, choices=TRAVEL_STYLES, default="balanced")
    pace = models.CharField(max_length=12, choices=PACES, default="moderate")
    companion = models.CharField(max_length=12, choices=COMPANIONS, default="solo")
    preferences = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT)
    ai_provider = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "-created_at"], name="trip_user_created_idx")]

    def __str__(self):
        return f"{self.destination} ({self.start_date})"

    def get_absolute_url(self):
        return reverse("trip_detail", args=[self.pk])

    @property
    def end_date(self):
        return self.start_date + timedelta(days=self.duration_days - 1)


class Itinerary(models.Model):
    class Status(models.TextChoices):
        OK = "ok", "OK"
        PARTIAL = "partial", "Partial"
        FAILED = "failed", "Failed"

    trip = models.OneToOneField(Trip, on_delete=models.CASCADE, related_name="itinerary")
    data = models.JSONField(default=dict)
    estimated_total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    generator = models.CharField(max_length=20, default="fallback")  # gemini | fallback
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OK)
    warnings = models.JSONField(default=list)
    generated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Itinerary for {self.trip}"
