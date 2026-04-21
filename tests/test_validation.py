import pytest


class TestIsValidSubdomain:
    def test_valid_simple(self, enumerator):
        assert enumerator._is_valid_subdomain("www.example.com") is True

    def test_valid_nested(self, enumerator):
        assert enumerator._is_valid_subdomain("api.v2.example.com") is True

    def test_valid_hyphen(self, enumerator):
        assert enumerator._is_valid_subdomain("my-app.example.com") is True

    def test_rejects_bare_ip(self, enumerator):
        assert enumerator._is_valid_subdomain("192.168.1.1") is False

    def test_rejects_url_with_scheme(self, enumerator):
        assert enumerator._is_valid_subdomain("https://www.example.com") is False

    def test_rejects_empty_string(self, enumerator):
        assert enumerator._is_valid_subdomain("") is False

    def test_rejects_html_entity(self, enumerator):
        assert enumerator._is_valid_subdomain("&amp;.example.com") is False

    def test_rejects_label_starting_with_dash(self, enumerator):
        assert enumerator._is_valid_subdomain("-bad.example.com") is False


class TestWildcardFiltering:
    def test_wildcard_ip_filtered_from_resolve(self, enumerator):
        from unittest.mock import patch, MagicMock

        wildcard_ip = "1.2.3.4"
        enumerator.wildcard_ips = {wildcard_ip}

        mock_answer = MagicMock()
        mock_answer.__str__ = lambda self: wildcard_ip

        mock_resolver = MagicMock()
        mock_resolver.resolve.return_value = [mock_answer]

        with patch.object(enumerator, 'get_resolver', return_value=mock_resolver):
            enumerator.__class__.resolve_domain.cache_clear()
            result = enumerator.resolve_domain("www.example.com")

        assert result is None or result == [], \
            "Wildcard IP should be filtered from resolve_domain result"
