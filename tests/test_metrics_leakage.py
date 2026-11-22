import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from oym.leakage import LeakageError, assert_no_leakage, find_overlap  # noqa: E402
from oym.metrics import cohen_kappa, tpr_tnr, wilson  # noqa: E402


def test_wilson_known_value():
    r = wilson(8, 10)
    assert abs(r.lo - 0.490) < 0.01 and abs(r.hi - 0.943) < 0.01


def test_wilson_edges():
    assert wilson(0, 20).lo == 0.0
    assert wilson(20, 20).hi == 1.0


def test_kappa():
    assert cohen_kappa(["a", "b", "a", "b"], ["a", "b", "a", "b"]) == 1.0
    assert abs(cohen_kappa(["a", "a", "b", "b"], ["a", "b", "a", "b"])) < 1e-9


def test_tpr_tnr():
    tpr, tnr = tpr_tnr([True, True, False, False], [True, False, False, True])
    assert tpr.k == 1 and tpr.n == 2 and tnr.k == 1 and tnr.n == 2


LETTER = ("I am writing to dispute the following accounts on my credit report because they are "
          "inaccurate and I never authorized them under the fair credit reporting act section 609")


def test_leakage_exact_and_near():
    train = {"t1": LETTER, "t2": "my mortgage servicer lost my payment twice this year"}
    test = {"q1": LETTER.upper(), "q2": LETTER.replace("609", "611"), "q3": "debt collector called my work"}
    hits = {h["test_id"]: h["kind"] for h in find_overlap(train, test)}
    assert hits.get("q1") == "exact" and hits.get("q2") == "near" and "q3" not in hits


def test_leakage_refuses():
    try:
        assert_no_leakage({"t": LETTER}, {"q": LETTER})
    except LeakageError:
        return
    raise AssertionError("expected LeakageError")
