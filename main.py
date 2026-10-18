
import os
from pathlib import Path

import yaml
from dotenv import dotenv_values
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DEFAULTS = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}

def to_bool(value):
    if isinstance(value, bool):
        return value
    return str(value).lower() in {"true", "1", "yes", "on"}

def coerce(key, value):
    if key in {"port", "workers"}:
        return int(value)
    if key == "debug":
        return to_bool(value)
    return str(value)

@app.get("/effective-config")
def effective_config(set: list[str] = Query(default=[])):
    config = DEFAULTS.copy()

    env_name = os.getenv("APP_ENV", "development")
    yaml_path = Path(f"config.{env_name}.yaml")

    if yaml_path.exists():
        with yaml_path.open(encoding="utf-8") as f:
            config.update(yaml.safe_load(f) or {})

    file_env = dotenv_values(".env")

    for key, value in file_env.items():
        if value is None:
            continue
        if key.startswith("APP_"):
            config[key[4:].lower()] = value
        elif key == "NUM_WORKERS":
            config["workers"] = value

    for key, value in os.environ.items():
        if key.startswith("APP_"):
            config[key[4:].lower()] = value

    for item in set:
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        config[key.strip().lower()] = value

    result = {}
    for key, value in config.items():
        if key == "api_key":
            result[key] = "****"
        else:
            result[key] = coerce(key, value)

    return result
