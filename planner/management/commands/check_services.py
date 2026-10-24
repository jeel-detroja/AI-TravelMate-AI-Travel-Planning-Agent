import datetime

from django.core.management.base import BaseCommand

from planner.services.geocoding import geocode
from planner.services.http import ServiceError
from planner.services.places import find_places
from planner.services.weather import get_weather


class Command(BaseCommand):
    help = "Probe the external services (makes real network calls). Use sparingly."

    def add_arguments(self, parser):
        parser.add_argument("--destination", default="Jaipur, India")

    def handle(self, *args, **opts):
        dest = opts["destination"]
        try:
            self.stdout.write(f"Geocoding '{dest}'...")
            geo = geocode(dest)
            if not geo:
                self.stderr.write("  FAILED: no result")
                return
            self.stdout.write(f"  OK: {geo['display_name']} ({geo['latitude']}, {geo['longitude']})")
            self.stdout.write("Fetching places...")
            places = find_places(geo["latitude"], geo["longitude"], ["history", "nature"])
            self.stdout.write(f"  OK: {len(places)} places")
            self.stdout.write("Fetching weather...")
            today = datetime.date.today()
            w = get_weather(geo["latitude"], geo["longitude"], today, today + datetime.timedelta(days=3))
            self.stdout.write(f"  available={w.get('available')} days={len(w.get('days', []))}")
        except ServiceError as exc:
            self.stderr.write(f"  FAILED: {exc}")
