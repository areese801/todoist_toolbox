"""Tests for URL detection in task content."""

from todoist.tui.snooze import extract_url


class TestExtractUrl:
    """Tests for extract_url()."""

    def test_http_url(self):
        """Extracts plain http URL."""
        assert extract_url("Visit http://example.com") == "http://example.com"

    def test_https_url(self):
        """Extracts https URL."""
        assert extract_url("See https://example.com/path") == "https://example.com/path"

    def test_url_with_query_params(self):
        """Extracts URL with query parameters."""
        text = "Check https://example.com/search?q=test&page=1"
        assert extract_url(text) == "https://example.com/search?q=test&page=1"

    def test_url_in_parentheses(self):
        """Extracts URL from within parentheses, stripping trailing paren."""
        text = "Details (https://example.com/info)"
        assert extract_url(text) == "https://example.com/info"

    def test_url_with_trailing_period(self):
        """Strips trailing period from URL."""
        text = "Visit https://example.com."
        assert extract_url(text) == "https://example.com"

    def test_url_with_trailing_comma(self):
        """Strips trailing comma from URL."""
        text = "See https://example.com, then proceed"
        assert extract_url(text) == "https://example.com"

    def test_no_url(self):
        """Returns None when no URL present."""
        assert extract_url("No URLs here") is None

    def test_empty_string(self):
        """Returns None for empty string."""
        assert extract_url("") is None

    def test_first_url_returned(self):
        """Returns the first URL when multiple are present."""
        text = "First https://first.com then https://second.com"
        assert extract_url(text) == "https://first.com"

    def test_url_with_fragment(self):
        """Extracts URL with fragment identifier."""
        text = "See https://example.com/page#section"
        assert extract_url(text) == "https://example.com/page#section"

    def test_url_with_port(self):
        """Extracts URL with port number."""
        text = "Server at http://localhost:8080/api"
        assert extract_url(text) == "http://localhost:8080/api"

    def test_markdown_link(self):
        """Extracts URL from markdown-style link text."""
        text = "Check [link](https://example.com/doc)"
        assert extract_url(text) == "https://example.com/doc"
