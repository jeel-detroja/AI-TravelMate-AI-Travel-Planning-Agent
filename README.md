# AI TravelMate — AI Travel Planning Agent

A Django web app that builds a personalised day-by-day itinerary from a destination, dates, budget and interests.

- **Geocoding:** Nominatim (OpenStreetMap)
- **Attractions:** Overpass API (OpenStreetMap) — real, named places only
- **Weather:** Open-Meteo (forecast ~16 days ahead; otherwise shown as unavailable)
- **Planner:** Google Gemini (optional) or a deterministic rule-based fallback. The AI can only choose from verified places; its output is validated server-side and **all costs are computed by the server**, never taken from the AI.
- **Maps:** Leaflet + OpenStreetMap tiles
- **Accounts:** sign up / log in / password reset (emails print to the console in dev), saved trips, regenerate, delete

## Quick start

Requires Python 3.10+ (3.12+ recommended).

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env             # Windows: copy .env.example .env
python manage.py migrate
python manage.py createsuperuser  # optional (for /admin/)
python manage.py runserver
```

Open http://127.0.0.1:8000/ , sign up, and click **Plan My Trip**. This needs internet access
(it calls Nominatim, Overpass and Open-Meteo). The first generation takes ~10–30 seconds.

If Django reports model changes not reflected in migrations, run `python manage.py makemigrations planner && python manage.py migrate`.

## Run the tests

```bash
python manage.py test
```

Tests mock all network calls, so they run offline.

## Check the live APIs

```bash
python manage.py check_services --destination "Jaipur, India"
```

## Enable Gemini (optional)

```bash
pip install google-genai
```

In `.env`:

```
AI_PROVIDER=gemini
GEMINI_API_KEY=your-key
GEMINI_MODEL=gemini-2.0-flash   # use a model your key supports
```

If Gemini is missing, misconfigured, or returns invalid output, the app silently uses the rule-based planner
(the itinerary page shows which one produced the plan).

## Production notes

- Set `DJANGO_DEBUG=False`, a strong `DJANGO_SECRET_KEY`, and `DJANGO_ALLOWED_HOSTS`.
- Set `DATABASE_URL` (e.g. Postgres) and `pip install "psycopg[binary]"`.
- Run `python manage.py collectstatic --noinput`; serve with `gunicorn config.wsgi`. WhiteNoise serves static files.
- Replace the in-memory cache with Redis/Memcached if you run several workers.
- Respect the usage policies of Nominatim and Overpass (set a real contact in `APP_USER_AGENT`; low traffic only).

## Known limitations

- Costs are rough, assumption-based estimates, not live prices or bookings.
- No opening hours, ticket prices, or traffic data.
- Generation is synchronous (the request waits). For heavy use, move it to a background worker.
- No per-day regenerate / swap-activity buttons; whole-trip regenerate only.
- Straight-line distances only; no turn-by-turn routing.

## Project layout

```
config/            Django settings, urls, wsgi/asgi
planner/           app: models, forms, views, services/, tests
planner/services/  geocoding, places, weather, budget, ai_planner, fallback_planner, pipeline
templates/         base, includes, planner pages, auth pages
static/            css/js (Leaflet map code in js/map.js)
```

Licence: MIT.
