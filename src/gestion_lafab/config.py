import os
from collections.abc import Mapping
from pathlib import Path

from dotenv import dotenv_values

PAHEKO_VARIABLES = ("PAHEKO_URL", "PAHEKO_API_ID", "PAHEKO_API_TOKEN")


def read_env() -> dict[str, str]:
    """The environment, overridden by `.env` in the working directory."""
    file_values = dotenv_values(Path.cwd() / ".env")
    return {**os.environ, **{k: v for k, v in file_values.items() if v is not None}}


def missing_variables(env: Mapping[str, str]) -> list[str]:
    return [name for name in PAHEKO_VARIABLES if not env.get(name)]
