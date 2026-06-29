import os

import pytest

from database import db


def test_requires_postgresql_database_url(monkeypatch):
    monkeypatch.delenv('DATABASE_URL', raising=False)
    with pytest.raises(RuntimeError, match='DATABASE_URL must be set'):
        db._get_database_url()


def test_rejects_non_postgresql_database_url(monkeypatch):
    monkeypatch.setenv('DATABASE_URL', 'sqlite:///tmp/test.db')
    with pytest.raises(RuntimeError, match='requires PostgreSQL'):
        db._get_database_url()


def test_accepts_postgresql_database_url(monkeypatch):
    monkeypatch.setenv('DATABASE_URL', 'postgresql://user:pass@localhost:5432/app')
    assert db._get_database_url() == 'postgresql://user:pass@localhost:5432/app'
