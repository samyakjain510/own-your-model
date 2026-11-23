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


def test_v2_formats_v1_missed():
    from oym.pii import scrub
    assert scrub("SSN 694 57 5617 here").text == "SSN [SSN] here"
    assert scrub("acct AC12345678 and 2672-5672-81").text == "acct [ACCOUNT] and [ACCOUNT]"
    assert scrub("sent to 12 N Oak St and 44 lakeview drive").text == "sent to [ADDRESS] and [ADDRESS]"


def test_v2_leaves_dates_amounts_and_filler_alone():
    from oym.pii import scrub
    for s in ["paid 300 to the court on 2024-03-14", "charged $1,250.00 on 03/14/2024 at 3:45 PM, ref 03-14",
              "made 2 payments on the way"]:
        assert scrub(s).text == s, s
