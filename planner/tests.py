import datetime
import json
from unittest import mock

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Trip
from .services import ai_planner, budget
from .services.fallback_planner import build_fallback_itinerary
from .services.routing import enrich_day_routes, estimate_transit, haversine_km

PLACES = [
    {
        "name": f"Place {i}",
        "category": "tourism:attraction",
        "latitude": 26.9 + i / 100,
        "longitude": 75.8 + i / 100,
        "source": "openstreetmap",
        "source_id": f"node/{i}",
        "attribution": "© OpenStreetMap contributors",
    }
    for i in range(1, 13)
]


def trip_payload(**over):
    base = {
        "destination": "Jaipur",
        "resolved_name": "Jaipur, India",
        "start_date": datetime.date.today(),
        "days": 2,
        "travellers": 2,
        "budget": 20000,
        "currency": "INR",
        "interests": ["history", "food"],
        "style": "balanced",
        "pace": "moderate",
        "companion": "couple",
        "max_activities": 4,
        "latitude": 26.9124,
        "longitude": 75.7873,
        "preferences": {
            "dietary": "Vegetarian",
            "accessibility": "Stroller friendly",
        },
    }
    base.update(over)
    return base


class BudgetTests(TestCase):
    def test_breakdown_sums_to_total(self):
        b = budget.estimate_breakdown("balanced", "INR", 2, 3, user_budget=30000)
        self.assertEqual(budget.q(sum(b["categories"].values())), b["total"])

    def test_summary_over_budget(self):
        s = budget.budget_summary(100, "USD", 150)
        self.assertTrue(s["over_budget"])
        self.assertEqual(s["status"], "over")

    def test_summary_healthy_buffer(self):
        s = budget.budget_summary(1000, "USD", 600)
        self.assertFalse(s["over_budget"])
        self.assertEqual(s["status"], "healthy")


class RoutingTests(TestCase):
    def test_haversine_calculation(self):
        # Jaipur center to Amber Fort approx 9-11 km
        dist = haversine_km(26.9124, 75.7873, 26.9855, 75.8513)
        self.assertGreater(dist, 5.0)
        self.assertLess(dist, 18.0)

    def test_estimate_transit(self):
        walk = estimate_transit(0.8)
        self.assertEqual(walk["mode"], "Walking")
        drive = estimate_transit(4.5)
        self.assertIn("Transit", drive["mode"])

    def test_enrich_day_routes(self):
        acts = [
            {"name": "Stop 1", "latitude": 26.91, "longitude": 75.78},
            {"name": "Stop 2", "latitude": 26.92, "longitude": 75.79},
        ]
        stats = enrich_day_routes(acts)
        self.assertGreater(stats["total_distance_km"], 0)
        self.assertIn("route_to_next", acts[0])
        self.assertNotIn("route_to_next", acts[1])


class PlannerTests(TestCase):
    def test_fallback_generates_days_and_routes(self):
        out = build_fallback_itinerary(trip_payload(), PLACES, {"available": False})
        self.assertEqual(len(out["days"]), 2)
        day1 = out["days"][0]
        self.assertIn("route_summary", day1)
        self.assertTrue(day1["morning"] or day1["afternoon"] or day1["evening"])

    def test_fallback_without_places_warns_cleanly(self):
        out = build_fallback_itinerary(trip_payload(), [], {"available": False})
        self.assertTrue(out["warnings"])
        self.assertEqual(len(out["days"]), 2)

    def test_ai_validation_and_normalization(self):
        raw = json.dumps(
            {
                "trip_summary": "An unforgettable royal exploration.",
                "days": [
                    {
                        "day_number": 1,
                        "title": "Heritage Fortresses",
                        "morning": [
                            {
                                "place_id": "node/1",
                                "name": "Amber Fort",
                                "category": "historic",
                                "activity": "Explore Amber Fort",
                                "description": "Marvel at the Sheesh Mahal mirror palace.",
                                "suggested_time": "09:30 AM",
                                "duration_minutes": 120,
                                "estimated_cost": 200,
                                "latitude": 26.985,
                                "longitude": 75.851,
                                "insider_tip": "Visit early to avoid crowds.",
                            }
                        ],
                        "afternoon": [],
                        "evening": [],
                        "dining_recommendations": [
                            {"name": "1135 AD", "cuisine": "Rajasthani", "meal": "Lunch"}
                        ],
                        "tips": ["Stay hydrated."],
                    },
                    {
                        "day_number": 2,
                        "title": "City Palaces & Bazaars",
                        "morning": [],
                        "afternoon": [
                            {
                                "place_id": "node/2",
                                "name": "City Palace",
                                "category": "historic",
                                "activity": "Visit City Palace",
                                "description": "Tour royal courtyards.",
                                "suggested_time": "02:00 PM",
                                "duration_minutes": 90,
                                "estimated_cost": 300,
                                "latitude": 26.925,
                                "longitude": 75.823,
                                "insider_tip": "Combo ticket saves time.",
                            }
                        ],
                        "evening": [],
                        "tips": ["Great shopping in Johari Bazaar."],
                    },
                ],
                "warnings": [],
            }
        )
        out = ai_planner._validate_and_normalize(raw, trip_payload(), PLACES)
        self.assertEqual(len(out["days"]), 2)
        self.assertEqual(out["generator"], "gemini")
        self.assertEqual(out["days"][0]["morning"][0]["name"], "Amber Fort")
        self.assertEqual(out["days"][0]["morning"][0]["estimated_cost"], 200)

    def test_ai_wrong_day_count_rejected(self):
        with self.assertRaises(ValueError):
            ai_planner._validate_and_normalize(json.dumps({"days": [{}]}), trip_payload(), PLACES)

    def test_malformed_ai_json_falls_back(self):
        cfg = {**settings.TRAVELMATE, "AI_PROVIDER": "gemini", "GEMINI_API_KEY": "dummy-key"}
        with override_settings(TRAVELMATE=cfg):
            with mock.patch.object(ai_planner, "_call_gemini", return_value="not json at all"):
                out = ai_planner.generate_itinerary(trip_payload(), PLACES, {"available": False})
        self.assertEqual(out["generator"], "fallback")


class ViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("alice", "a@example.com", "pw-12345-xyz")
        self.other = User.objects.create_user("bob", "b@example.com", "pw-12345-xyz")

    def form_data(self, **over):
        data = {
            "destination": "Jaipur, India",
            "start_date": (datetime.date.today() + datetime.timedelta(days=3)).isoformat(),
            "duration_days": 2,
            "budget": "50000",
            "currency": "INR",
            "travellers": 2,
            "interests": ["history", "food"],
            "travel_style": "balanced",
            "pace": "moderate",
            "companion": "couple",
            "dietary": "Vegetarian",
        }
        data.update(over)
        return data

    def test_public_pages(self):
        for name in ("home", "about", "how_it_works", "privacy", "health", "login", "signup"):
            self.assertEqual(self.client.get(reverse(name)).status_code, 200, name)

    def test_login_required(self):
        r = self.client.get(reverse("create_trip"))
        self.assertEqual(r.status_code, 302)
        self.assertIn("/accounts/login/", r["Location"])

    def test_signup_creates_user_and_logs_in(self):
        r = self.client.post(
            reverse("signup"),
            {
                "username": "carol",
                "email": "c@example.com",
                "password1": "Str0ng-pass-99",
                "password2": "Str0ng-pass-99",
            },
        )
        self.assertRedirects(r, reverse("saved_trips"))

    def test_past_date_rejected(self):
        self.client.force_login(self.user)
        r = self.client.post(reverse("create_trip"), self.form_data(start_date="2000-01-01"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "cannot be in the past")

    @mock.patch("planner.services.pipeline.get_weather", return_value={"available": False, "days": []})
    @mock.patch("planner.services.pipeline.find_places", return_value=PLACES)
    @mock.patch(
        "planner.services.pipeline.geocode",
        return_value={"display_name": "Jaipur, India", "latitude": 26.9, "longitude": 75.8},
    )
    def test_full_flow_and_ownership(self, *_):
        self.client.force_login(self.user)
        r = self.client.post(reverse("create_trip"), self.form_data())
        trip = Trip.objects.get(user=self.user)
        self.assertRedirects(r, reverse("trip_detail", args=[trip.pk]))
        page = self.client.get(reverse("trip_detail", args=[trip.pk]))
        self.assertContains(page, "Day 1")
        self.assertContains(page, "map-markers")
        self.assertContains(page, "map-routes")
        self.assertEqual(self.client.get(reverse("saved_trips")).status_code, 200)

        # Another user cannot see / delete it
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(reverse("trip_detail", args=[trip.pk])).status_code, 404)
        self.client.post(reverse("delete_trip", args=[trip.pk]))
        self.assertTrue(Trip.objects.filter(pk=trip.pk).exists())

        # Owner can regenerate and delete
        self.client.force_login(self.user)
        self.assertEqual(self.client.post(reverse("regenerate_trip", args=[trip.pk])).status_code, 302)
        self.client.post(reverse("delete_trip", args=[trip.pk]))
        self.assertFalse(Trip.objects.filter(pk=trip.pk).exists())

    @mock.patch("planner.services.pipeline.geocode", return_value=None)
    def test_unknown_destination_shows_error(self, _):
        self.client.force_login(self.user)
        r = self.client.post(reverse("create_trip"), self.form_data(destination="Xyzzyplugh"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Could not find")
        self.assertFalse(Trip.objects.exists())
