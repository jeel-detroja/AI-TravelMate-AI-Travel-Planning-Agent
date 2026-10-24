import django.core.validators
import django.db.models.deletion
from decimal import Decimal

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Trip",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("destination", models.CharField(max_length=160)),
                ("resolved_name", models.CharField(blank=True, max_length=255)),
                ("latitude", models.FloatField(blank=True, null=True)),
                ("longitude", models.FloatField(blank=True, null=True)),
                ("start_date", models.DateField()),
                (
                    "duration_days",
                    models.PositiveSmallIntegerField(
                        validators=[
                            django.core.validators.MinValueValidator(1),
                            django.core.validators.MaxValueValidator(14),
                        ]
                    ),
                ),
                (
                    "budget",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=12,
                        validators=[django.core.validators.MinValueValidator(Decimal("0.01"))],
                    ),
                ),
                (
                    "currency",
                    models.CharField(
                        choices=[
                            ("INR", "INR — Indian Rupee"),
                            ("USD", "USD — US Dollar"),
                            ("EUR", "EUR — Euro"),
                            ("GBP", "GBP — British Pound"),
                        ],
                        default="INR",
                        max_length=3,
                    ),
                ),
                (
                    "travellers",
                    models.PositiveSmallIntegerField(
                        default=1,
                        validators=[
                            django.core.validators.MinValueValidator(1),
                            django.core.validators.MaxValueValidator(20),
                        ],
                    ),
                ),
                ("interests", models.JSONField(default=list)),
                (
                    "travel_style",
                    models.CharField(
                        choices=[("budget", "Budget"), ("balanced", "Balanced"), ("premium", "Premium")],
                        default="balanced",
                        max_length=12,
                    ),
                ),
                (
                    "pace",
                    models.CharField(
                        choices=[("relaxed", "Relaxed"), ("moderate", "Moderate"), ("packed", "Packed")],
                        default="moderate",
                        max_length=12,
                    ),
                ),
                (
                    "companion",
                    models.CharField(
                        choices=[
                            ("solo", "Solo"),
                            ("couple", "Couple"),
                            ("family", "Family"),
                            ("friends", "Friends"),
                        ],
                        default="solo",
                        max_length=12,
                    ),
                ),
                ("preferences", models.JSONField(blank=True, default=dict)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("draft", "Draft"),
                            ("generating", "Generating"),
                            ("ready", "Ready"),
                            ("failed", "Failed"),
                        ],
                        default="draft",
                        max_length=12,
                    ),
                ),
                ("ai_provider", models.CharField(blank=True, max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="trips",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="Itinerary",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("data", models.JSONField(default=dict)),
                ("estimated_total_cost", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("generator", models.CharField(default="fallback", max_length=20)),
                (
                    "status",
                    models.CharField(
                        choices=[("ok", "OK"), ("partial", "Partial"), ("failed", "Failed")],
                        default="ok",
                        max_length=10,
                    ),
                ),
                ("warnings", models.JSONField(default=list)),
                ("generated_at", models.DateTimeField(auto_now=True)),
                (
                    "trip",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="itinerary",
                        to="planner.trip",
                    ),
                ),
            ],
        ),
        migrations.AddIndex(
            model_name="trip",
            index=models.Index(fields=["user", "-created_at"], name="trip_user_created_idx"),
        ),
    ]
