# tests/test_config.py
import os
import pytest
from app.config import get_settings

def test_settings_load():
    os.environ["META_VERIFY_TOKEN"] = "test_token"
    os.environ["OPENROUTER_API_KEY"] = "sk-or-test"
    settings = get_settings()
    assert settings.META_VERIFY_TOKEN == "test_token"
    assert settings.OPENROUTER_API_KEY == "sk-or-test"
