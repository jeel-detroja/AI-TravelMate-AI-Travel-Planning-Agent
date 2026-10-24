INTERESTS = [
    ("nature", "Nature"),
    ("history", "History & Culture"),
    ("food", "Food"),
    ("adventure", "Adventure"),
    ("shopping", "Shopping"),
    ("architecture", "Architecture"),
    ("spiritual", "Spiritual Places"),
    ("beaches", "Beaches"),
    ("nightlife", "Nightlife"),
    ("family", "Family Activities"),
    ("photography", "Photography"),
]
INTEREST_KEYS = {k for k, _ in INTERESTS}

TRAVEL_STYLES = [("budget", "Budget"), ("balanced", "Balanced"), ("premium", "Premium")]
PACES = [("relaxed", "Relaxed"), ("moderate", "Moderate"), ("packed", "Packed")]
COMPANIONS = [
    ("solo", "Solo"),
    ("couple", "Couple"),
    ("family", "Family"),
    ("friends", "Friends"),
]
CURRENCIES = [
    ("INR", "INR — Indian Rupee (₹)"),
    ("USD", "USD — US Dollar ($)"),
    ("EUR", "EUR — Euro (€)"),
    ("GBP", "GBP — British Pound (£)"),
]
CURRENCY_KEYS = {k for k, _ in CURRENCIES}
CURRENCY_SYMBOLS = {
    "INR": "₹",
    "USD": "$",
    "EUR": "€",
    "GBP": "£",
}

MAX_DURATION_DAYS = 14
MAX_TRAVELLERS = 20

PACE_ACTIVITIES_COUNT = {
    "relaxed": 3,
    "moderate": 4,
    "packed": 5,
}

# Color palette for map routes per day
DAY_COLORS = [
    "#2563eb",  # Day 1: Blue
    "#0d9488",  # Day 2: Teal
    "#7c3aed",  # Day 3: Purple
    "#ea580c",  # Day 4: Deep Orange
    "#db2777",  # Day 5: Rose
    "#16a34a",  # Day 6: Emerald
    "#0284c7",  # Day 7: Sky Blue
    "#d97706",  # Day 8: Amber
    "#4f46e5",  # Day 9: Indigo
    "#059669",  # Day 10: Jade
    "#e11d48",  # Day 11: Crimson
    "#84cc16",  # Day 12: Lime
    "#8b5cf6",  # Day 13: Violet
    "#0891b2",  # Day 14: Cyan
]

# Maps interests -> OSM tag filters for Overpass
INTEREST_OSM_TAGS = {
    "nature": [
        '["leisure"="park"]',
        '["leisure"="nature_reserve"]',
        '["leisure"="garden"]',
        '["natural"="waterfall"]',
        '["natural"="peak"]',
        '["tourism"="viewpoint"]',
    ],
    "history": [
        '["historic"]',
        '["tourism"="museum"]',
        '["historic"="castle"]',
        '["historic"="monument"]',
        '["historic"="memorial"]',
        '["historic"="ruins"]',
        '["historic"="archaeological_site"]',
    ],
    "food": [
        '["amenity"="restaurant"]',
        '["amenity"="cafe"]',
        '["amenity"="marketplace"]',
        '["amenity"="food_court"]',
    ],
    "adventure": [
        '["tourism"="attraction"]',
        '["natural"="peak"]',
        '["leisure"="water_park"]',
        '["sport"="climbing"]',
    ],
    "shopping": [
        '["shop"="mall"]',
        '["amenity"="marketplace"]',
        '["shop"="department_store"]',
    ],
    "architecture": [
        '["tourism"="attraction"]',
        '["historic"="monument"]',
        '["historic"="castle"]',
        '["building"="cathedral"]',
        '["tourism"="gallery"]',
    ],
    "spiritual": [
        '["amenity"="place_of_worship"]',
        '["historic"="monastery"]',
    ],
    "beaches": [
        '["natural"="beach"]',
        '["leisure"="resort"]',
    ],
    "nightlife": [
        '["amenity"="bar"]',
        '["amenity"="nightclub"]',
        '["amenity"="pub"]',
    ],
    "family": [
        '["tourism"="theme_park"]',
        '["tourism"="zoo"]',
        '["tourism"="aquarium"]',
        '["leisure"="park"]',
        '["leisure"="water_park"]',
    ],
    "photography": [
        '["tourism"="viewpoint"]',
        '["tourism"="attraction"]',
        '["historic"="monument"]',
    ],
}

DEFAULT_OSM_TAGS = [
    '["tourism"="attraction"]',
    '["tourism"="museum"]',
    '["historic"]',
    '["tourism"="viewpoint"]',
    '["leisure"="park"]',
]
