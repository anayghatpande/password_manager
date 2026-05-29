import re
from password_generator import generate_password


class TestPasswordGenerator:
    def test_generates_string(self):
        pw = generate_password()
        assert isinstance(pw, str)
        assert len(pw) > 0

    def test_pattern_matches(self):
        pw = generate_password()
        assert re.match(r"^[A-Z][a-z]+\d{2}[!@#$%&*][A-Z][a-z]+$", pw)

    def test_different_each_call(self):
        pws = {generate_password() for _ in range(100)}
        assert len(pws) == 100

    def test_length_reasonable(self):
        pw = generate_password()
        assert 10 <= len(pw) <= 20
