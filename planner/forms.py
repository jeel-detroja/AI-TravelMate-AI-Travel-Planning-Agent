import datetime
from decimal import Decimal
import re

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .constants import (
    COMPANIONS,
    CURRENCIES,
    CURRENCY_KEYS,
    INTEREST_KEYS,
    INTERESTS,
    MAX_DURATION_DAYS,
    MAX_TRAVELLERS,
    PACES,
    TRAVEL_STYLES,
)

_W = {"class": "form-control"}
_S = {"class": "form-select"}


class SignupForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={**_W, "placeholder": "name@example.com"}),
    )

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class TripForm(forms.Form):
    destination = forms.CharField(
        max_length=160,
        widget=forms.TextInput(attrs={**_W, "placeholder": "e.g. Jaipur, India or Paris, France"}),
    )
    start_date = forms.DateField(widget=forms.DateInput(attrs={**_W, "type": "date"}))
    duration_days = forms.IntegerField(
        min_value=1,
        max_value=MAX_DURATION_DAYS,
        initial=3,
        widget=forms.NumberInput(attrs={**_W, "min": 1, "max": MAX_DURATION_DAYS}),
    )
    budget = forms.DecimalField(
        min_value=Decimal("1.00"),
        max_value=Decimal("100000000.00"),
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={**_W, "placeholder": "e.g. 25000"}),
    )
    currency = forms.ChoiceField(choices=CURRENCIES, initial="INR", widget=forms.Select(attrs=_S))
    travellers = forms.IntegerField(
        min_value=1,
        max_value=MAX_TRAVELLERS,
        initial=2,
        widget=forms.NumberInput(attrs={**_W, "min": 1, "max": MAX_TRAVELLERS}),
    )
    interests = forms.MultipleChoiceField(
        choices=INTERESTS, widget=forms.CheckboxSelectMultiple, required=True
    )
    travel_style = forms.ChoiceField(
        choices=TRAVEL_STYLES, initial="balanced", widget=forms.Select(attrs=_S)
    )
    pace = forms.ChoiceField(choices=PACES, initial="moderate", widget=forms.Select(attrs=_S))
    companion = forms.ChoiceField(
        choices=COMPANIONS, initial="couple", widget=forms.Select(attrs=_S)
    )
    # Optional personal preferences
    dietary = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={**_W, "placeholder": "e.g. Vegetarian, Halal, Vegan, Gluten-Free"}),
    )
    accessibility = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={**_W, "placeholder": "e.g. Wheelchair accessible, low walking, elevator-only"}),
    )
    max_activities = forms.IntegerField(
        min_value=1,
        max_value=8,
        required=False,
        widget=forms.NumberInput(attrs={**_W, "placeholder": "e.g. 3 or 4"}),
    )

    def clean_destination(self):
        d = self.cleaned_data["destination"].strip()
        # Sanitize against control characters or script injection
        d = re.sub(r"[\r\n\t]+", " ", d)
        if not d or len(d) < 2:
            raise forms.ValidationError("Please provide a valid destination city or region.")
        return d

    def clean_start_date(self):
        d = self.cleaned_data["start_date"]
        if d < datetime.date.today():
            raise forms.ValidationError("Start date cannot be in the past.")
        return d

    def clean_currency(self):
        c = self.cleaned_data["currency"]
        if c not in CURRENCY_KEYS:
            raise forms.ValidationError("Unsupported currency.")
        return c

    def clean_interests(self):
        vals = self.cleaned_data["interests"]
        if any(v not in INTEREST_KEYS for v in vals):
            raise forms.ValidationError("Invalid interest selection.")
        return vals

    def clean_dietary(self):
        val = self.cleaned_data.get("dietary", "").strip()
        return re.sub(r"[\r\n\t]+", " ", val)[:200]

    def clean_accessibility(self):
        val = self.cleaned_data.get("accessibility", "").strip()
        return re.sub(r"[\r\n\t]+", " ", val)[:200]
