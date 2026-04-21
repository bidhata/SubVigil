import json
import csv
import pytest
from unittest.mock import patch


SAMPLE_SUBDOMAIN_INFO = {
    "www.example.com": {
        "subdomain": "www.example.com",
        "active": True,
        "status_code": 200,
        "server": "nginx",
        "title": "Example",
        "ip": "1.2.3.4",
        "ip_owner": "Example ISP",
        "ssh_open": False,
        "takeover_vulnerable": False,
        "ports": [80, 443],
    },
    "dead.example.com": {
        "subdomain": "dead.example.com",
        "active": False,
        "status_code": None,
        "server": None,
        "title": None,
        "ip": None,
        "ip_owner": "",
        "ssh_open": False,
        "takeover_vulnerable": False,
        "ports": [],
    },
}


@pytest.fixture
def populated_enumerator(enumerator, tmp_path):
    enumerator.subdomain_info = SAMPLE_SUBDOMAIN_INFO.copy()
    enumerator.subdomains = set(SAMPLE_SUBDOMAIN_INFO.keys())
    enumerator.active_subdomains = {"www.example.com"}
    enumerator.inactive_subdomains = {"dead.example.com"}
    enumerator.ssh_enabled = set()
    enumerator.takeover_candidates = set()
    enumerator.takeover_reasons = {}
    enumerator.output_dir = str(tmp_path)
    return enumerator


def test_json_report_has_required_keys(populated_enumerator):
    with patch.object(populated_enumerator, 'generate_html_report'):
        populated_enumerator.generate_reports()

    import os
    json_path = os.path.join(populated_enumerator.output_dir, "scan_results.json")
    assert os.path.exists(json_path), "scan_results.json not created"
    with open(json_path) as f:
        data = json.load(f)
    assert "domain" in data
    assert "subdomains" in data
    assert "www.example.com" in data["subdomains"]


def test_csv_report_has_correct_headers(populated_enumerator):
    with patch.object(populated_enumerator, 'generate_html_report'):
        populated_enumerator.generate_reports()

    import os
    csv_path = os.path.join(populated_enumerator.output_dir, "scan_results.csv")
    assert os.path.exists(csv_path), "scan_results.csv not created"
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        headers = next(reader)
    assert "Subdomain" in headers
    assert "Active" in headers
    assert "IP" in headers


def test_active_txt_contains_active_subdomain(populated_enumerator):
    with patch.object(populated_enumerator, 'generate_html_report'):
        populated_enumerator.generate_reports()

    import os
    active_path = os.path.join(populated_enumerator.output_dir, "active_subdomains.txt")
    assert os.path.exists(active_path)
    content = open(active_path).read()
    assert "www.example.com" in content
    assert "dead.example.com" not in content
