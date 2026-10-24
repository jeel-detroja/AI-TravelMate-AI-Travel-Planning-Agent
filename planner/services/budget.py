from decimal import ROUND_HALF_UP, Decimal

from ..constants import CURRENCY_SYMBOLS


def D(x):
    return Decimal(str(x))


_Q = Decimal("0.01")

# Realistic per-person-per-day baseline benchmarks by travel style and currency
STYLE_BENCHMARKS = {
    "INR": {"budget": D(2200), "balanced": D(5500), "premium": D(14000)},
    "USD": {"budget": D(50), "balanced": D(130), "premium": D(320)},
    "EUR": {"budget": D(45), "balanced": D(120), "premium": D(290)},
    "GBP": {"budget": D(40), "balanced": D(105), "premium": D(260)},
}

# Standard allocation percentages of travel budget
CATEGORY_SPLIT = {
    "accommodation": D("0.38"),
    "food": D("0.28"),
    "transportation": D("0.14"),
    "admission": D("0.12"),
    "other": D("0.08"),
}


def q(amount):
    return D(amount).quantize(_Q, rounding=ROUND_HALF_UP)


def estimate_breakdown(style, currency, travellers, days, user_budget=None):
    """Compute an itemized cost estimate tailored to style, duration, group size,
    and the user's allocated budget."""
    c = currency if currency in STYLE_BENCHMARKS else "USD"
    benchmarks = STYLE_BENCHMARKS.get(c, STYLE_BENCHMARKS["USD"])
    person_days = D(max(travellers, 1)) * D(max(days, 1))

    # Base target daily spend per person
    default_daily = benchmarks.get(style, benchmarks["balanced"])

    if user_budget is not None and D(user_budget) > Decimal("0.01"):
        user_daily = D(user_budget) / person_days
        # Blend user budget with benchmark for balanced realism (70% user budget, 30% baseline)
        blended_daily = q(user_daily * D("0.85") + default_daily * D("0.15"))
        total = q(user_budget)
    else:
        blended_daily = q(default_daily)
        total = q(blended_daily * person_days)

    categories = {
        cat: q(total * share)
        for cat, share in CATEGORY_SPLIT.items()
    }

    # Ensure sum of categories matches total exactly
    cat_sum = sum(categories.values())
    if cat_sum != total:
        diff = total - cat_sum
        categories["other"] = q(categories["other"] + diff)

    symbol = CURRENCY_SYMBOLS.get(currency, currency)
    assumptions = (
        f"Estimated for a '{style}' style in {currency} ({symbol}{blended_daily}/person/day) "
        f"across {days} day(s) for {travellers} traveller(s). Covers stay, food, transit & activities."
    )

    return {
        "currency": currency,
        "currency_symbol": symbol,
        "per_person_per_day": blended_daily,
        "categories": categories,
        "total": total,
        "assumptions": assumptions,
    }


def budget_summary(trip_budget, currency, estimated_total, activity_costs=0):
    """Provide realistic budget analysis and actionable guidance."""
    total = q(trip_budget)
    est = q(estimated_total)
    remaining = q(total - est)
    over_budget = est > total
    symbol = CURRENCY_SYMBOLS.get(currency, currency)

    if total > Decimal("0.00"):
        ratio = est / total
        pct_diff = round(float((total - est) / total) * 100, 1)
    else:
        ratio = Decimal("1.0")
        pct_diff = 0.0

    if ratio <= Decimal("0.85"):
        status = "healthy"
        status_label = "Comfortable Buffer"
        badge_class = "success"
        advice = f"You have a healthy {pct_diff}% contingency buffer for shopping, fine dining, or spontaneous activities."
    elif ratio <= Decimal("1.02"):
        status = "balanced"
        status_label = "On Track"
        badge_class = "teal"
        advice = "Your budget is well-calibrated for the planned activities and travel style."
    elif ratio <= Decimal("1.20"):
        status = "tight"
        status_label = "Slightly Tight"
        badge_class = "warning"
        advice = "Slightly tight for this style. Opting for public transit or local bistros will keep you within budget."
    else:
        status = "over"
        status_label = "Over Budget"
        badge_class = "danger"
        advice = "Estimated expenses exceed your target budget. Consider relaxing paid entry activities or booking stays early."

    return {
        "total_budget": total,
        "estimated": est,
        "remaining": remaining,
        "over_budget": over_budget,
        "currency": currency,
        "currency_symbol": symbol,
        "status": status,
        "status_label": status_label,
        "badge_class": badge_class,
        "pct_diff": pct_diff,
        "advice": advice,
        "activity_costs": q(activity_costs),
    }
