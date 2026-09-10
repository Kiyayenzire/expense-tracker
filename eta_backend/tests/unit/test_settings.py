import importlib
import os


def test_localhost_hosts_are_enabled_by_default(monkeypatch):
    monkeypatch.delenv('DJANGO_ALLOWED_HOSTS', raising=False)
    monkeypatch.delenv('DJANGO_DEBUG', raising=False)

    import backend.settings as settings_module

    reloaded_settings = importlib.reload(settings_module)

    assert 'localhost' in reloaded_settings.ALLOWED_HOSTS
    assert '127.0.0.1' in reloaded_settings.ALLOWED_HOSTS
