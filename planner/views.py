import datetime
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .constants import DAY_COLORS
from .forms import SignupForm, TripForm
from .models import Itinerary, Trip
from .services.budget import budget_summary
from .services.pipeline import generate_for_trip
from .services.routing import external_nav_url


def home(request):
    return render(request, "planner/home.html")


def about(request):
    return render(request, "planner/about.html")


def how_it_works(request):
    return render(request, "planner/how_it_works.html")


def privacy(request):
    return render(request, "planner/privacy.html")


def health(request):
    return JsonResponse({"status": "ok"})


def _rate_limited(request, bucket, limit, window=60):
    """Accurate rate limiting preventing infinite sliding window issues."""
    identifier = request.user.pk if request.user.is_authenticated else request.META.get("REMOTE_ADDR", "anon")
    key = f"rl:{bucket}:{identifier}"
    try:
        if cache.add(key, 1, window):
            return False
        count = cache.incr(key)
        return count > limit
    except Exception:
        count = cache.get(key, 0)
        if count >= limit:
            return True
        cache.set(key, count + 1, window)
        return False


def signup(request):
    if request.user.is_authenticated:
        return redirect("saved_trips")
    if request.method == "POST" and _rate_limited(request, "signup", limit=10, window=300):
        messages.error(request, "Too many registration attempts. Please try again in a few minutes.")
        return render(request, "registration/signup.html", {"form": SignupForm()})

    form = SignupForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Welcome to AI TravelMate! Start by planning your first adventure.")
        return redirect("saved_trips")
    return render(request, "registration/signup.html", {"form": form})


def _run_generation(trip):
    """Run the pipeline and persist the result. Returns the warnings list."""
    itinerary, weather, warnings = generate_for_trip(trip)
    if itinerary is None:
        trip.status = Trip.Status.FAILED
        trip.save(update_fields=["status"])
        return warnings

    itinerary["weather"] = weather
    Itinerary.objects.update_or_create(
        trip=trip,
        defaults={
            "data": itinerary,
            "estimated_total_cost": Decimal(str(itinerary.get("estimated_total_cost", 0))),
            "generator": itinerary.get("generator", "fallback"),
            "warnings": warnings,
            "status": Itinerary.Status.PARTIAL if warnings else Itinerary.Status.OK,
        },
    )
    trip.status = Trip.Status.READY
    trip.ai_provider = itinerary.get("generator", "fallback")
    trip.save(update_fields=["status", "ai_provider"])
    return warnings


@login_required
def create_trip(request):
    form = TripForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        if _rate_limited(request, "generate", limit=10, window=60):
            messages.error(request, "Too many trip generations in a short period. Please wait 60 seconds.")
            return render(request, "planner/create_trip.html", {"form": form})

        cd = form.cleaned_data
        trip = Trip.objects.create(
            user=request.user,
            destination=cd["destination"],
            start_date=cd["start_date"],
            duration_days=cd["duration_days"],
            budget=cd["budget"],
            currency=cd["currency"],
            travellers=cd["travellers"],
            interests=cd["interests"],
            travel_style=cd["travel_style"],
            pace=cd["pace"],
            companion=cd["companion"],
            status=Trip.Status.GENERATING,
            preferences={
                "dietary": cd.get("dietary", ""),
                "accessibility": cd.get("accessibility", ""),
                "max_activities": cd.get("max_activities"),
            },
        )
        warnings = _run_generation(trip)
        if trip.status == Trip.Status.FAILED:
            trip.delete()
            for w in warnings:
                messages.error(request, w)
            return render(request, "planner/create_trip.html", {"form": form})

        messages.success(request, f"Your personalized itinerary for {trip.destination} is ready!")
        return redirect("trip_detail", pk=trip.pk)

    return render(request, "planner/create_trip.html", {"form": form})


@login_required
def trip_detail(request, pk):
    trip = get_object_or_404(Trip, pk=pk, user=request.user)
    itinerary = getattr(trip, "itinerary", None)
    budget = None
    markers = []
    routes = []
    day_colors = {}

    if itinerary:
        ticket_costs = itinerary.data.get("activity_ticket_costs", 0)
        budget = budget_summary(
            trip.budget, trip.currency, itinerary.estimated_total_cost, activity_costs=ticket_costs
        )

        for day in itinerary.data.get("days", []):
            day_num = day.get("day_number", 1)
            color = DAY_COLORS[(day_num - 1) % len(DAY_COLORS)]
            day_colors[day_num] = color
            day_coords = []
            act_idx = 1

            for slot in ("morning", "afternoon", "evening"):
                for act in day.get(slot, []):
                    lat = act.get("latitude")
                    lon = act.get("longitude")
                    if lat is not None and lon is not None:
                        try:
                            lat = float(lat)
                            lon = float(lon)
                            day_coords.append([lat, lon])
                            markers.append(
                                {
                                    "name": str(act.get("name", "Stop")),
                                    "activity": str(act.get("activity", act.get("name", "Stop"))),
                                    "cat": str(act.get("category", "attraction")),
                                    "day": day_num,
                                    "order": act_idx,
                                    "lat": lat,
                                    "lon": lon,
                                    "color": color,
                                    "suggested_time": str(act.get("suggested_time", "")),
                                    "tip": str(act.get("insider_tip", "")),
                                    "nav": external_nav_url(lat, lon),
                                }
                            )
                            act_idx += 1
                        except (ValueError, TypeError):
                            continue

            if len(day_coords) > 1:
                routes.append(
                    {
                        "day": day_num,
                        "color": color,
                        "coordinates": day_coords,
                    }
                )

    center = (
        {"lat": float(trip.latitude), "lon": float(trip.longitude)}
        if trip.latitude is not None and trip.longitude is not None
        else None
    )

    return render(
        request,
        "planner/itinerary.html",
        {
            "trip": trip,
            "itinerary": itinerary,
            "budget": budget,
            "markers": markers,
            "routes": routes,
            "day_colors": day_colors,
            "center": center,
        },
    )


@login_required
def saved_trips(request):
    trips = Trip.objects.filter(user=request.user)
    today = datetime.date.today()
    upcoming = [t for t in trips if t.end_date >= today]
    past = [t for t in trips if t.end_date < today]
    return render(request, "planner/saved_trips.html", {"upcoming": upcoming, "past": past})


@login_required
@require_POST
def regenerate_trip(request, pk):
    trip = get_object_or_404(Trip, pk=pk, user=request.user)
    if _rate_limited(request, "generate", limit=10, window=60):
        messages.error(request, "Please wait a moment before regenerating again.")
        return redirect("trip_detail", pk=pk)

    trip.status = Trip.Status.GENERATING
    trip.save(update_fields=["status"])
    _run_generation(trip)
    if trip.status == Trip.Status.FAILED:
        messages.error(request, "Could not regenerate the itinerary. Please try again.")
    else:
        messages.success(request, "Itinerary successfully regenerated with fresh recommendations!")
    return redirect("trip_detail", pk=pk)


@login_required
@require_POST
def delete_trip(request, pk):
    trip = get_object_or_404(Trip, pk=pk, user=request.user)
    trip.delete()
    messages.success(request, f"Trip to '{trip.destination}' was deleted.")
    return redirect("saved_trips")


def handler404(request, exception):
    return render(request, "planner/404.html", status=404)


def handler500(request):
    return render(request, "planner/500.html", status=500)
