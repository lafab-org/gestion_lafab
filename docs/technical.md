# Technique

## Pile

- Python 3.13, géré avec uv.
- Serveur : Litestar, gabarits Jinja2. Écoute sur `127.0.0.1:8000`.
- Pages : HTML rendu par le serveur, interactivité avec Datastar. Le
  fichier JavaScript de Datastar est servi par l'application.
- Accès aux API : httpx.
- Paheko : l'API de `https://lafab.paheko.cloud`, en lecture seule.
  La Lecture Paheko tient en une seule requête SQL.
  La Lecture des initiations aussi.
  Le Rapprochement des initiations lit dans Paheko les membres, les
  inscriptions aux activités d'initiation et les lignes de caisse de
  la catégorie 5 « D - Initiations » (tables `plugin_pos_*` de
  l'extension Caisse).
- TiBillet : aucun accès à l'API ; l'Export des tickets est envoyé par
  l'utilisateur et n'est pas enregistré sur le disque.
- CSV du rapprochement : UTF-8, séparateur virgule, chaque valeur entre
  guillemets, fins de ligne CRLF.
- Graphiques : SVG produit par le serveur, sans bibliothèque
  JavaScript.
- L'Historique des adhésions est le fichier
  `src/gestion_lafab/data/historique_adhesions.csv` : une ligne par
  année, l'année puis les 12 nombres mensuels.

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
- Tests de l'interface dans un navigateur avec Playwright
  (`pytest-playwright`, Chromium sans affichage).
- Vérifications : `uv run pytest`, `uv run ruff check`,
  `uv run ruff format --check`.
