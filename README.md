# gestion_lafab

Application web locale qui automatise des tâches de gestion de
La Fabrique (Strasbourg) à partir de Paheko et de TiBillet.

Spécification : [docs/](docs/README.md).

## Installation

Nécessite [uv](https://docs.astral.sh/uv/). Créer un fichier `.env`
avec `PAHEKO_URL`, `PAHEKO_API_ID` et `PAHEKO_API_TOKEN`.

## Utilisation

```sh
uv run gestion-lafab
```

## Tests

```sh
uv run pytest
uv run ruff check
uv run ruff format --check
```
