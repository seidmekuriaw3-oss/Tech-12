import sys
import types

import pytest

import run


def test_init_database_uses_database_db_init_db(monkeypatch):
    calls = []

    def fake_init_db():
        calls.append("called")

    import database.db as database_db
    monkeypatch.setattr(database_db, "init_db", fake_init_db)

    app_module = types.ModuleType("app")
    monkeypatch.setitem(sys.modules, "app", app_module)

    assert run.init_database() is True
    assert calls == ["called"]
