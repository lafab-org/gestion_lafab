# Technique

## Pile

- Python 3.13, géré avec uv.
- Serveur : Litestar, gabarits Jinja2. Écoute sur `127.0.0.1:8000`.
- Pages : HTML rendu par le serveur, interactivité avec Datastar. Le
  fichier JavaScript de Datastar est servi par l'application.
- Accès aux API : httpx. Calculs statistiques : pandas.
- Paheko : l'API de `https://lafab.paheko.cloud`, en lecture seule.

## Lancement et configuration

- `uv run gestion-lafab` démarre le serveur et ouvre la page d'accueil
  dans le navigateur.
- La configuration est lue dans un fichier `.env` du répertoire de
  travail, hors de git : `PAHEKO_URL`, `PAHEKO_API_ID`,
  `PAHEKO_API_TOKEN`.

## Conventions

- Documents du projet, interface et messages en français ; code,
  identifiants et commentaires en anglais.
- La spécification donne le texte exact des messages affichés.
- Code dans `src/gestion_lafab/`, tests dans `tests/`.

## Tests et qualité

- Tests avec pytest ; l'API Paheko y est simulée, jamais appelée.
- Vérifications : `uv run pytest`, `uv run ruff check`,
  `uv run ruff format --check`.
