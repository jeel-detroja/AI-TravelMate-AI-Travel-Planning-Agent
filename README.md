# 🌍 AI TravelMate — AI-Powered Travel Planning Agent

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.1%2B-092E20.svg?logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Google Gemini](https://img.shields.io/badge/Google%20Gemini-AI%20Powered-orange.svg?logo=google-gemini&logoColor=white)](https://ai.google.dev/)
[![OpenStreetMap](https://img.shields.io/badge/OpenStreetMap-Nominatim%20%7C%20Overpass-7EBC6F.svg?logo=openstreetmap&logoColor=white)](https://www.openstreetmap.org/)
[![Leaflet](https://img.shields.io/badge/Leaflet-Interactive%20Maps-199900.svg?logo=leaflet&logoColor=white)](https://leafletjs.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**AI TravelMate** is a full-featured travel planning platform powered by Django and Google Gemini. It automatically generates verified, day-by-day itineraries customized to your destination, travel dates, budget, interests, companion type, and travel pace.

Unlike typical AI travel apps that hallucinate places and invent unrealistic costs, AI TravelMate grounds its planning in **real-world geospatial data** and uses a **deterministic server-side calculation engine** for verified budgets and schedules.

---

## 🌟 Key Features

- **📍 Verified Real-World Places (Zero Hallucination)**:
  - Validates destinations using **Nominatim (OpenStreetMap)** geocoding.
  - Fetches real attractions, cultural spots, and landmarks via **Overpass API (OSM)** within the target radius. The AI selects only verified, existing coordinates and venues.

- **🤖 Intelligent Hybrid Planning Engine**:
  - Leverages **Google Gemini** (`gemini-2.5-flash`, `gemini-2.0-flash`) with structured JSON schema outputs.
  - Built-in multi-model cascading fallback and a **deterministic rule-based engine** that seamlessly takes over if API quotas are reached or if offline.

- **💰 Deterministic Server-Side Budgeting**:
  - The AI never estimates or calculates finances.
  - The server algorithmically computes tiered breakdowns (accommodations, daily meals, local transit, entry fees, and emergency contingency buffers) across **Budget**, **Moderate**, and **Luxury** tiers.

- **🌤️ Live Weather Forecasts**:
  - Integrated with **Open-Meteo** to display real-time weather forecasts (temperature, precipitation, conditions) for up to 16 days ahead.

- **🗺️ Interactive Map & Visual Itinerary**:
  - Embedded **Leaflet.js** map with custom markers, coordinates, and day-by-day route paths.

- **👤 User Accounts & Trip Management**:
  - Full authentication workflow: Sign up, Log in, Password reset (console-printed in dev).
  - Save trips to your dashboard, re-generate itineraries with different criteria, or delete past plans.

---

## 🏗️ Architecture & Pipeline

```text
User Input (Destination, Dates, Budget, Interests, Style, Pace)
                             │
                             ▼
              1. Geocoding Service (Nominatim)
           [Validates coords & display name]
                             │
                             ▼
           2. Places & POI Retrieval (Overpass API)
            [Fetches verified cultural & leisure POIs]
                             │
                             ▼
             3. Weather Service (Open-Meteo)
           [Fetches live forecast up to 16 days]
                             │
                             ▼
         4. Planning Engine (Google Gemini / Fallback)
         [Assembles daily activity sequence from verified POIs]
                             │
                             ▼
              5. Server-Side Budget Engine
          [Calculates deterministic cost estimates]
                             │
                             ▼
            Stored in Database & Rendered to User
           [Interactive Leaflet Map + Daily Timeline]
```

---

## 🧰 Tech Stack

| Component | Technology | Purpose |
| :--- | :--- | :--- |
| **Backend Framework** | [Django 5.1+](https://www.djangoproject.com/) | Web framework, ORM, authentication, and routing |
| **AI / LLM** | [Google GenAI SDK](https://github.com/google-gemini/generative-ai-python) | Generates context-aware, personalized daily itineraries |
| **Geocoding & POIs** | [OpenStreetMap Nominatim](https://nominatim.org/) & [Overpass API](https://overpass-api.de/) | Destination verification and real-world attraction lookup |
| **Weather API** | [Open-Meteo](https://open-meteo.com/) | Live, keyless weather forecasts |
| **Mapping & Frontend**| [Leaflet.js](https://leafletjs.com/) + HTML5 / CSS3 / Vanilla JS | Interactive maps, responsive design, and itinerary UI |
| **Static & Serving** | WhiteNoise, Gunicorn | Production static file serving and WSGI HTTP server |
| **Database** | SQLite (Development) / PostgreSQL (Production) | Trip and user persistence |

---

## 🚀 Quick Start Guide

### Prerequisites
- **Python 3.10+** (Python 3.12+ recommended)
- **Git**
- Active internet connection (for Nominatim, Overpass, and Open-Meteo API queries)

### 1. Clone the Repository
```bash
git clone https://github.com/jeel-detroja/AI-TravelMate-AI-Travel-Planning-Agent.git
cd AI-TravelMate-AI-Travel-Planning-Agent
```

### 2. Set Up Virtual Environment

**On Windows (PowerShell / Command Prompt):**
```powershell
python -m venv .venv
.venv\Scripts\activate
```

**On macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy the template configuration file:

**Windows:**
```powershell
copy .env.example .env
```

**macOS / Linux:**
```bash
cp .env.example .env
```

Open `.env` and set your preferred options (see [Configuration](#-configuration--environment-variables)).

### 5. Run Database Migrations
```bash
python manage.py migrate
```

*(Optional) Create an administrator account:*
```bash
python manage.py createsuperuser
```

### 6. Start the Development Server
```bash
python manage.py runserver
```

Visit **http://127.0.0.1:8000/** in your browser, create an account, and plan your first trip!

---

## ⚙️ Configuration & Environment Variables

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `DJANGO_SECRET_KEY` | *(Random string)* | Unique secret key for Django security. |
| `DJANGO_DEBUG` | `True` | Set to `False` in production. |
| `DJANGO_ALLOWED_HOSTS` | `127.0.0.1,localhost` | Comma-separated list of allowed host domains. |
| `DATABASE_URL` | *(Empty)* | PostgreSQL connection URL (e.g. `postgres://user:pass@host:5432/db`). Leave empty for local SQLite. |
| `AI_PROVIDER` | `gemini` | `gemini` or `fallback` (for deterministic offline/rule-based generation). |
| `GEMINI_API_KEY` | *(Empty)* | Your Google Gemini API key from [Google AI Studio](https://aistudio.google.com/). |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Gemini model name (e.g., `gemini-2.5-flash`, `gemini-2.0-flash`). |
| `APP_USER_AGENT` | `AI-TravelMate/1.0 (...)` | User-Agent string sent to OpenStreetMap / Overpass API. |
| `NOMINATIM_BASE_URL` | `https://nominatim.openstreetmap.org` | OpenStreetMap Nominatim endpoint. |
| `OVERPASS_URL` | `https://overpass-api.de/api/interpreter` | Overpass API query interpreter endpoint. |
| `OPEN_METEO_URL` | `https://api.open-meteo.com/v1/forecast` | Open-Meteo weather endpoint. |
| `HTTP_TIMEOUT` | `15` | External API request timeout in seconds. |

---

## 🧪 Testing & Diagnostics

### Run the Automated Test Suite
All network calls in tests are mocked, allowing them to run offline quickly:
```bash
python manage.py test
```

### Verify Live External Services
Test real-time connectivity to Nominatim, Overpass API, and Open-Meteo:
```bash
python manage.py check_services --destination "Jaipur, India"
```

### Verify Gemini API Key & Available Models
Run the bundled diagnostic script to list models accessible to your API key:
```bash
python check_gemini.py
```

---

## 📁 Project Structure

```text
ai-travelmate/
├── config/                 # Django project settings, URLs, WSGI/ASGI handlers
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── planner/                # Main application package
│   ├── management/commands # Custom management tools (check_services)
│   ├── migrations/         # Database migrations
│   ├── services/           # Core business logic & integrations
│   │   ├── ai_planner.py       # Google Gemini integration & response parsing
│   │   ├── fallback_planner.py # Deterministic offline planning algorithm
│   │   ├── geocoding.py        # Nominatim geocoding & caching
│   │   ├── places.py           # Overpass API POI queries
│   │   ├── weather.py          # Open-Meteo weather forecasts
│   │   ├── budget.py           # Algorithmic cost estimator
│   │   ├── routing.py          # Coordinate distance & route helpers
│   │   └── pipeline.py         # Complete workflow orchestrator
│   ├── forms.py            # Form validation (trips, preferences)
│   ├── models.py           # Trip & itinerary database models
│   ├── views.py            # View controllers & rate limiting
│   └── tests.py            # Unit & integration test cases
├── static/                 # Static assets (custom CSS & Leaflet map.js)
├── templates/              # HTML templates (Django template language)
│   ├── planner/            # Trip planning, detail, saved trips views
│   └── registration/       # Auth views (login, signup, password reset)
├── check_gemini.py         # Utility script to test Gemini API key
├── manage.py               # Django CLI utility
├── requirements.txt        # Python package dependencies
└── README.md               # Project documentation
```

---

## 🔒 Production Deployment Notes

1. **Security**:
   - Set `DJANGO_DEBUG=False`.
   - Generate a strong, random `DJANGO_SECRET_KEY`.
   - Set `DJANGO_SECURE_SSL=True` when serving over HTTPS.
   - Configure valid hostnames in `DJANGO_ALLOWED_HOSTS`.
2. **Database**:
   - Install PostgreSQL adapter: `pip install "psycopg[binary]"` and set `DATABASE_URL`.
3. **Static Files & Web Server**:
   - Run `python manage.py collectstatic --noinput`.
   - Serve using an ASGI/WSGI production server such as **Gunicorn**:
     ```bash
     gunicorn config.wsgi:application --bind 0.0.0.0:8000
     ```
4. **API Fair Usage**:
   - Provide a valid contact email in `APP_USER_AGENT` to comply with the OpenStreetMap and Nominatim usage policies.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
