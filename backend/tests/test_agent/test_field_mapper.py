"""Tests for the field mapper that maps user profile to form fields."""


from app.services.agent.field_mapper import FieldMapper


class TestFieldMapperProperties:
    """Tests for direct property access on the mapper."""

    def test_maps_first_name(self, user_profile):
        mapper = FieldMapper(user_profile)
        assert mapper.first_name == "John"

    def test_maps_last_name(self, user_profile):
        mapper = FieldMapper(user_profile)
        assert mapper.last_name == "Doe"

    def test_maps_email(self, user_profile):
        mapper = FieldMapper(user_profile)
        assert mapper.email == "john.doe@example.com"

    def test_maps_phone(self, user_profile):
        mapper = FieldMapper(user_profile)
        assert mapper.phone == "+1-555-123-4567"

    def test_maps_linkedin(self, user_profile):
        mapper = FieldMapper(user_profile)
        assert mapper.linkedin_url == "https://linkedin.com/in/johndoe"

    def test_missing_optional_field_returns_none(self):
        mapper = FieldMapper({"first_name": "Alice"})
        assert mapper.phone is None
        assert mapper.linkedin_url is None


class TestGetFieldValue:
    """Tests for fuzzy field name matching."""

    def test_exact_match(self, user_profile):
        mapper = FieldMapper(user_profile)
        assert mapper.get_field_value("email") == "john.doe@example.com"

    def test_case_insensitive(self, user_profile):
        mapper = FieldMapper(user_profile)
        assert mapper.get_field_value("Email") == "john.doe@example.com"
        assert mapper.get_field_value("FIRST_NAME") == "John"

    def test_pattern_matching_firstname(self, user_profile):
        mapper = FieldMapper(user_profile)
        assert mapper.get_field_value("firstname") == "John"
        assert mapper.get_field_value("given_name") == "John"

    def test_pattern_matching_lastname(self, user_profile):
        mapper = FieldMapper(user_profile)
        assert mapper.get_field_value("lastname") == "Doe"
        assert mapper.get_field_value("surname") == "Doe"

    def test_pattern_matching_phone(self, user_profile):
        mapper = FieldMapper(user_profile)
        assert mapper.get_field_value("telephone") == "+1-555-123-4567"
        assert mapper.get_field_value("mobile") == "+1-555-123-4567"

    def test_pattern_matching_linkedin(self, user_profile):
        mapper = FieldMapper(user_profile)
        result = mapper.get_field_value("linkedin_profile")
        assert result == "https://linkedin.com/in/johndoe"

    def test_unknown_field_returns_none(self, user_profile):
        mapper = FieldMapper(user_profile)
        assert mapper.get_field_value("favorite_color") is None


class TestMapFields:
    """Tests for batch field mapping."""

    def test_maps_known_fields(self, user_profile):
        mapper = FieldMapper(user_profile)
        result = mapper.map_fields(["email", "phone", "first_name"])
        assert len(result) == 3
        assert result["email"] == "john.doe@example.com"

    def test_skips_unknown_fields(self, user_profile):
        mapper = FieldMapper(user_profile)
        result = mapper.map_fields(["email", "unknown_field"])
        assert len(result) == 1
        assert "unknown_field" not in result

    def test_empty_form_fields(self, user_profile):
        mapper = FieldMapper(user_profile)
        result = mapper.map_fields([])
        assert result == {}


class TestFormatPhone:
    """Tests for phone number formatting."""

    def test_us_format(self, user_profile):
        mapper = FieldMapper(user_profile)
        assert mapper.format_phone("us") == "(555) 123-4567"

    def test_digits_format(self, user_profile):
        mapper = FieldMapper(user_profile)
        assert mapper.format_phone("digits") == "5551234567"

    def test_no_phone_returns_none(self):
        mapper = FieldMapper({"first_name": "Alice"})
        assert mapper.format_phone() is None

    def test_non_standard_phone_returns_original(self):
        mapper = FieldMapper({"phone": "+44 20 7123 4567"})
        # Non-US phone numbers returned as-is
        assert mapper.format_phone() == "+44 20 7123 4567"
