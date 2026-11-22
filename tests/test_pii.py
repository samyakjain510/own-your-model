import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from oym.pii import scrub  # noqa: E402


def test_email_phone_ssn():
    r = scrub("Email me at jane.doe@example.com or call (312) 555-0199. SSN 123-45-6789.")
    assert "[EMAIL]" in r.text and "[PHONE]" in r.text and "[SSN]" in r.text
    assert "example.com" not in r.text


def test_card_requires_luhn():
    good = scrub("card 4111 1111 1111 1111 was charged")
    assert "[CARD]" in good.text
    bad = scrub("ref 1234 5678 9012 3456 noted")  # fails Luhn
    assert "[CARD]" not in bad.text


def test_cfpb_mask():
    r = scrub("On XX/XX/XXXX I called XXXX XXXX about my loan.")
    assert "XXXX" not in r.text
    assert r.counts["CFPB_MASK"] == 3


def test_plain_text_untouched():
    text = "I disputed the late fee twice and nobody answered."
    assert scrub(text).text == text
