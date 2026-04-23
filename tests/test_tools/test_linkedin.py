import pytest
import io
from tools.linkedin import parse_csv

def test_parse_csv_standard_columns():
    csv_content = "email,first_name,last_name,title,company\nceo@acme.io,Jane,Doe,CEO,Acme\n"
    leads = parse_csv(io.StringIO(csv_content))
    assert len(leads) == 1
    assert leads[0]["email"] == "ceo@acme.io"
    assert leads[0]["source"] == "csv"

def test_parse_csv_skips_missing_email():
    csv_content = "email,first_name,last_name\n,Jane,Doe\nceo@acme.io,John,Smith\n"
    leads = parse_csv(io.StringIO(csv_content))
    assert len(leads) == 1
    assert leads[0]["email"] == "ceo@acme.io"

def test_parse_csv_optional_linkedin_url():
    csv_content = "email,first_name,linkedin_url\nceo@acme.io,Jane,https://linkedin.com/in/jane\n"
    leads = parse_csv(io.StringIO(csv_content))
    assert leads[0]["linkedin_url"] == "https://linkedin.com/in/jane"

def test_parse_csv_empty_linkedin_url_becomes_none():
    csv_content = "email,first_name,linkedin_url\nceo@acme.io,Jane,\n"
    leads = parse_csv(io.StringIO(csv_content))
    assert leads[0]["linkedin_url"] is None
