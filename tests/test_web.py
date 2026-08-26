"""HTML and JSON API tests for the FastAPI front-end. Isolated tmp store."""

from fastapi.testclient import TestClient

from app.domain import OPENING_BALANCE_CENTS
from app.store import JsonStore
from app.web import app, get_store


def _client_for(tmp_path) -> TestClient:
    store = JsonStore(tmp_path / "balance.json")
    app.dependency_overrides[get_store] = lambda: store
    return TestClient(app)


def setup_function():
    app.dependency_overrides.clear()


def teardown_function():
    app.dependency_overrides.clear()


def test_opening_balance_html(tmp_path):
    client = _client_for(tmp_path)
    response = client.get("/")
    assert response.status_code == 200
    assert "Account Management" in response.text
    assert "$1,000.00" in response.text


def test_opening_balance_json(tmp_path):
    client = _client_for(tmp_path)
    response = client.get("/api/balance")
    assert response.status_code == 200
    body = response.json()
    assert body["balance_cents"] == OPENING_BALANCE_CENTS
    assert body["balance"] == "$1,000.00"


def test_credit_100_then_new_balance(tmp_path):
    client = _client_for(tmp_path)
    response = client.post("/credit", data={"amount": "100.00"}, follow_redirects=True)
    assert response.status_code == 200
    assert "$1,100.00" in response.text
    assert client.get("/api/balance").json()["balance_cents"] == 110_000


def test_debit_50(tmp_path):
    client = _client_for(tmp_path)
    response = client.post("/debit", data={"amount": "50.00"}, follow_redirects=True)
    assert response.status_code == 200
    assert "$950.00" in response.text
    assert client.get("/api/balance").json()["balance_cents"] == 95_000


def test_debit_2000_insufficient_funds_balance_unchanged(tmp_path):
    client = _client_for(tmp_path)
    client.post("/credit", data={"amount": "100.00"}, follow_redirects=True)
    client.post("/debit", data={"amount": "50.00"}, follow_redirects=True)
    response = client.post("/debit", data={"amount": "2000.00"})
    assert response.status_code == 200
    assert "Insufficient funds for this debit." in response.text
    assert "$1,050.00" in response.text
    assert client.get("/api/balance").json()["balance_cents"] == 105_000
    assert client.get("/api/balance").json()["balance"] == "$1,050.00"


def test_zero_credit_and_debit_allowed(tmp_path):
    client = _client_for(tmp_path)
    credit = client.post("/credit", data={"amount": "0.00"}, follow_redirects=True)
    assert credit.status_code == 200
    assert "$1,000.00" in credit.text
    debit = client.post("/debit", data={"amount": "0"}, follow_redirects=True)
    assert debit.status_code == 200
    assert "$1,000.00" in debit.text
    assert client.get("/api/balance").json()["balance_cents"] == OPENING_BALANCE_CENTS


def test_credit_debit_flow_json(tmp_path):
    client = _client_for(tmp_path)
    credited = client.post("/api/credit", json={"amount": "100.00"})
    assert credited.status_code == 200
    assert credited.json()["balance_cents"] == 110_000
    debited = client.post("/api/debit", json={"amount": "50.00"})
    assert debited.status_code == 200
    assert debited.json()["balance"] == "$1,050.00"
    refused = client.post("/api/debit", json={"amount": "2000.00"})
    assert refused.status_code == 409
    assert refused.json()["detail"] == "Insufficient funds for this debit."
    assert client.get("/api/balance").json()["balance_cents"] == 105_000


def test_invalid_amount_re_renders_with_error(tmp_path):
    client = _client_for(tmp_path)
    response = client.post("/credit", data={"amount": "abc"})
    assert response.status_code == 400
    assert "Invalid amount" in response.text
    assert client.get("/api/balance").json()["balance_cents"] == OPENING_BALANCE_CENTS


def test_transactions_listed_after_credit(tmp_path):
    client = _client_for(tmp_path)
    client.post("/credit", data={"amount": "100.00"}, follow_redirects=True)
    page = client.get("/")
    assert "credit" in page.text
    assert "$100.00" in page.text
    ledger = client.get("/api/transactions")
    assert ledger.status_code == 200
    items = ledger.json()["transactions"]
    assert len(items) == 1
    assert items[0]["type"] == "credit"
    assert items[0]["amount_cents"] == 10_000


def test_web_tests_do_not_touch_default_store(tmp_path):
    client = _client_for(tmp_path)
    client.post("/credit", data={"amount": "100.00"}, follow_redirects=True)
    assert (tmp_path / "balance.json").exists()
