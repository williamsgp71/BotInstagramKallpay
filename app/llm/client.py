# app/llm/client.py
from functools import lru_cache
import yaml
from openai import AsyncOpenAI
from app.config import get_settings

@lru_cache(maxsize=1)
def load_yaml_config():
    with open("config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

@lru_cache(maxsize=None)
def _get_client(base_url: str, api_key: str) -> AsyncOpenAI:
    return AsyncOpenAI(api_key=api_key, base_url=base_url)

async def get_llm_response(prompt_system: str, prompt_user: str, history: list = None) -> str:
    config = load_yaml_config()
    settings = get_settings()
    provider_name = config.get("active_provider", "openrouter")
    
    # Resolver endpoint y API Key
    if provider_name == "openrouter":
        base_url = config["providers"]["openrouter"]["base_url"]
        api_key = settings.OPENROUTER_API_KEY
    elif provider_name == "deepseek":
        base_url = config["providers"]["deepseek"]["base_url"]
        api_key = settings.DEEPSEEK_API_KEY
    elif provider_name == "openai":
        base_url = config["providers"]["openai"]["base_url"]
        api_key = settings.OPENAI_API_KEY
    else:
        raise ValueError(f"Proveedor no soportado: {provider_name}")
    
    model = config.get("active_model") or config["providers"][provider_name]["model"]

    client = _get_client(base_url, api_key)

    messages = [{"role": "system", "content": prompt_system}]
    if history:
        for msg in history:
            role = "user" if msg.sender_type == "user" else "assistant"
            messages.append({"role": role, "content": msg.content})
    
    messages.append({"role": "user", "content": prompt_user})
    
    response = await client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=config.get("temperature", 0.7)
    )
    return response.choices[0].message.content
