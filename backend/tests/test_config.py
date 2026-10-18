"""Tests for environment configuration and origins parser."""

import os
import pytest
from app.config import Settings, parse_origins


def test_parse_origins_empty():
    assert parse_origins("") == []
    assert parse_origins("   ") == []


def test_parse_origins_wildcard():
    assert parse_origins("*") == ["*"]
    assert parse_origins("  *  ") == ["*"]


def test_parse_origins_multiple():
    raw = "http://localhost:5173, https://app.example.com , http://127.0.0.1:5173"
    expected = ["http://localhost:5173", "https://app.example.com", "http://127.0.0.1:5173"]
    assert parse_origins(raw) == expected


def test_settings_env_override(monkeypatch):
    monkeypatch.setenv("PORT", "9000")
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("LOG_LEVEL", "warning")
    monkeypatch.setenv("ALLOWED_ORIGINS", "https://farm.example.com")

    custom_settings = Settings()
    assert custom_settings.PORT == 9000
    assert custom_settings.ENVIRONMENT == "production"
    assert custom_settings.LOG_LEVEL == "warning"
    assert custom_settings.ALLOWED_ORIGINS == ["https://farm.example.com"]
