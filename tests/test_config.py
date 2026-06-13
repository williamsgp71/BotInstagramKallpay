# tests/test_config.py
import os
import pytest
from app.config import get_settings

@pytest.fixture(autouse=True)
def clear_config_cache():
    get_settings.cache_clear()
    # Save original env
    old_verify = os.environ.get("META_VERIFY_TOKEN")
    old_or = os.environ.get("OPENROUTER_API_KEY")
    yield
    get_settings.cache_clear()
    # Restore original env
    if old_verify is not None:
        os.environ["META_VERIFY_TOKEN"] = old_verify
    else:
        os.environ.pop("META_VERIFY_TOKEN", None)
    if old_or is not None:
        os.environ["OPENROUTER_API_KEY"] = old_or
    else:
        os.environ.pop("OPENROUTER_API_KEY", None)

def test_settings_load():
    os.environ["META_VERIFY_TOKEN"] = "test_token"
    os.environ["OPENROUTER_API_KEY"] = "sk-or-test"
    settings = get_settings()
    assert settings.META_VERIFY_TOKEN == "test_token"
    assert settings.OPENROUTER_API_KEY == "sk-or-test"

