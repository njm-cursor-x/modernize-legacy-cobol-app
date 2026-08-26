"""FastAPI HTML front-end for the COBOL-equivalent account menu."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from app.domain import AccountService, InsufficientFundsError, format_money, parse_amount_to_cents
from app.store import DEFAULT_STORE_PATH, JsonStore, Transaction

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

INVALID_AMOUNT_MESSAGE = "Invalid amount. Please enter a non-negative number."

app = FastAPI(title="Account Management System")


def get_store() -> JsonStore:
    return JsonStore(DEFAULT_STORE_PATH)


class AmountBody(BaseModel):
    amount: str = Field(..., min_length=1)


def _transaction_view(tx: Transaction) -> dict:
    return {
        "type": tx.type,
        "amount": format_money(tx.amount_cents),
        "amount_cents": tx.amount_cents,
        "balance": format_money(tx.resulting_balance_cents),
        "resulting_balance_cents": tx.resulting_balance_cents,
        "timestamp": tx.timestamp,
    }


def _page_context(store: JsonStore, error: Optional[str] = None) -> dict:
    service = AccountService(store)
    balance_cents = service.get_balance()
    transactions = [_transaction_view(tx) for tx in reversed(store.list_transactions())]
    return {
        "balance": format_money(balance_cents),
        "balance_cents": balance_cents,
        "transactions": transactions,
        "error": error,
    }


def _render_index(
    request: Request,
    store: JsonStore,
    error: Optional[str] = None,
    status_code: int = 200,
) -> HTMLResponse:
    context = _page_context(store, error=error)
    return templates.TemplateResponse(request, "index.html", context, status_code=status_code)


def _parse_amount(raw: str) -> int:
    try:
        return parse_amount_to_cents(raw)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=INVALID_AMOUNT_MESSAGE) from exc


@app.get("/", response_class=HTMLResponse)
def index(request: Request, store: JsonStore = Depends(get_store)) -> HTMLResponse:
    return _render_index(request, store)


@app.post("/credit")
def credit_form(
    request: Request,
    amount: str = Form(...),
    store: JsonStore = Depends(get_store),
):
    try:
        cents = parse_amount_to_cents(amount)
    except ValueError:
        return _render_index(request, store, error=INVALID_AMOUNT_MESSAGE, status_code=400)
    AccountService(store).credit(cents)
    return RedirectResponse("/", status_code=303)


@app.post("/debit")
def debit_form(
    request: Request,
    amount: str = Form(...),
    store: JsonStore = Depends(get_store),
):
    try:
        cents = parse_amount_to_cents(amount)
    except ValueError:
        return _render_index(request, store, error=INVALID_AMOUNT_MESSAGE, status_code=400)
    try:
        AccountService(store).debit(cents)
    except InsufficientFundsError as exc:
        return _render_index(request, store, error=str(exc))
    return RedirectResponse("/", status_code=303)


@app.get("/api/balance")
def api_balance(store: JsonStore = Depends(get_store)) -> dict:
    balance_cents = AccountService(store).get_balance()
    return {"balance_cents": balance_cents, "balance": format_money(balance_cents)}


@app.post("/api/credit")
def api_credit(body: AmountBody, store: JsonStore = Depends(get_store)) -> dict:
    cents = _parse_amount(body.amount)
    balance_cents = AccountService(store).credit(cents)
    return {"balance_cents": balance_cents, "balance": format_money(balance_cents)}


@app.post("/api/debit")
def api_debit(body: AmountBody, store: JsonStore = Depends(get_store)) -> dict:
    cents = _parse_amount(body.amount)
    try:
        balance_cents = AccountService(store).debit(cents)
    except InsufficientFundsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"balance_cents": balance_cents, "balance": format_money(balance_cents)}


@app.get("/api/transactions")
def api_transactions(store: JsonStore = Depends(get_store)) -> dict:
    return {"transactions": [_transaction_view(tx) for tx in store.list_transactions()]}
