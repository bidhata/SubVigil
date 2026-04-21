from pathlib import Path


def test_whoisxml_uses_regex_not_lstrip():
    """modules/05_whoisxml.py must use re.sub for wildcard stripping, not lstrip."""
    src = (Path(__file__).parent.parent / "modules" / "05_whoisxml.py").read_text()
    assert "lstrip" not in src, "Replace lstrip('*.') with re.sub(r'^(\\*.)+', '', ...)"
    assert "re.sub" in src
