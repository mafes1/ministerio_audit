"""Common Selenium actions shared across experiments."""

from __future__ import annotations


def login_infojobs(driver, username: str, password: str) -> None:
    """Log in to Infojobs with the provided credentials."""
    raise NotImplementedError


def search_offers(driver, query: str) -> None:
    """Search for offers using a query string."""
    raise NotImplementedError


def apply_to_offer(driver, offer_url: str) -> None:
    """Apply to a specific offer URL."""
    raise NotImplementedError
