import pytest
from unittest.mock import patch, MagicMock


def test_takeover_services_has_no_generic_404_indicator(enumerator):
    """The takeover_services dict must not contain bare '404' or 'Not Found' as indicators."""
    for service, indicators in enumerator.takeover_services.items():
        for ind in indicators:
            assert ind.strip() != "404", (
                f"{service} has bare '404' indicator — too generic, causes false positives"
            )
            assert ind.strip() != "Not Found", (
                f"{service} has 'Not Found' indicator — too generic, causes false positives"
            )


def test_known_service_dangling_cname_triggers_takeover(enumerator):
    """A dangling CNAME to a known service must flag takeover."""
    sub = "app.example.com"

    mock_resolver = MagicMock()
    mock_cname = MagicMock()
    mock_cname.target.__str__ = lambda self: "myapp.github.io"
    mock_resolver.resolve.side_effect = [
        [mock_cname],
        Exception("NXDOMAIN"),
    ]

    with patch.object(enumerator, 'get_resolver', return_value=mock_resolver):
        result = enumerator.check_subdomain_takeover(sub)

    assert result is True, "Dangling CNAME to github.io must flag takeover"


def test_unknown_service_cname_does_not_trigger_takeover(enumerator):
    """A CNAME to an unknown service must not flag takeover."""
    sub = "blog.example.com"

    mock_resolver = MagicMock()
    mock_cname = MagicMock()
    mock_cname.target.__str__ = lambda self: "some-unknown-random-service.com"
    mock_resolver.resolve.side_effect = [
        [mock_cname],
        Exception("NXDOMAIN"),
    ]

    with patch.object(enumerator, 'get_resolver', return_value=mock_resolver):
        result = enumerator.check_subdomain_takeover(sub)

    assert result is False, "Unknown service CNAME should not trigger takeover"
