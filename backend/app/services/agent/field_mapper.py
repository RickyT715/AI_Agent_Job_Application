"""Maps user profile data to form field values.

Extracts structured fields (name, email, phone, etc.) from the user profile
dict and prepares them for form filling.
"""

import re

# Common form field name patterns mapped to profile keys
FIELD_PATTERNS: dict[str, list[str]] = {
    "first_name": ["first_name", "firstname", "first name", "given_name", "fname"],
    "last_name": ["last_name", "lastname", "last name", "family_name", "surname", "lname"],
    "email": ["email", "email_address", "e-mail"],
    "phone": ["phone", "phone_number", "telephone", "mobile", "cell"],
    "linkedin_url": ["linkedin", "linkedin_url", "linkedin_profile"],
    "resume_text": ["resume", "resume_text", "cover_letter"],
    "location": ["location", "city", "address"],
    "website": ["website", "portfolio", "personal_website", "url"],
}


class FieldMapper:
    """Maps user profile fields to form input fields."""

    def __init__(self, user_profile: dict[str, str]) -> None:
        self._profile = user_profile

    @property
    def first_name(self) -> str | None:
        return self._profile.get("first_name")

    @property
    def last_name(self) -> str | None:
        return self._profile.get("last_name")

    @property
    def email(self) -> str | None:
        return self._profile.get("email")

    @property
    def phone(self) -> str | None:
        return self._profile.get("phone")

    @property
    def linkedin_url(self) -> str | None:
        return self._profile.get("linkedin_url")

    def get_field_value(self, field_name: str) -> str | None:
        """Look up a profile value by form field name.

        Tries exact match first, then fuzzy pattern matching.

        Args:
            field_name: The form field name/label to look up.

        Returns:
            The matching profile value, or None if not found.
        """
        normalized = field_name.lower().strip()

        # Exact match against profile keys
        if normalized in self._profile:
            return self._profile[normalized]

        # Pattern matching: check if field_name matches known patterns
        for profile_key, patterns in FIELD_PATTERNS.items():
            for pattern in patterns:
                if pattern in normalized or normalized in pattern:
                    value = self._profile.get(profile_key)
                    if value is not None:
                        return value

        return None

    def map_fields(self, form_fields: list[str]) -> dict[str, str]:
        """Map a list of form field names to profile values.

        Args:
            form_fields: List of form field names/labels.

        Returns:
            Dict of field_name → value for fields that could be mapped.
        """
        mapped: dict[str, str] = {}
        for field in form_fields:
            value = self.get_field_value(field)
            if value is not None:
                mapped[field] = value
        return mapped

    def get_all_mappable_fields(self) -> dict[str, str]:
        """Return all profile fields that have values.

        Returns:
            Dict of profile_key → value for all non-empty fields.
        """
        return {k: v for k, v in self._profile.items() if v}

    def format_phone(self, format_type: str = "us") -> str | None:
        """Format phone number for a specific locale.

        Args:
            format_type: "us" for (555) 123-4567, "digits" for 5551234567.

        Returns:
            Formatted phone string or None.
        """
        phone = self.phone
        if not phone:
            return None

        # Strip to digits only
        digits = re.sub(r"\D", "", phone)

        # Remove leading country code "1" if present
        if len(digits) == 11 and digits.startswith("1"):
            digits = digits[1:]

        if len(digits) != 10:
            return phone  # Return original if not standard US format

        if format_type == "digits":
            return digits
        # Default US format
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
