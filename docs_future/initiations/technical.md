# Technique

## Pile

- Paheko : l'API de `https://lafab.paheko.cloud`, en lecture seule. …
  La Lecture Paheko tient en une seule requête SQL. …
  La Lecture des initiations aussi. …
  Le Rapprochement des initiations lit dans Paheko les membres, les
  inscriptions aux activités d'initiation et les lignes de caisse de
  la catégorie 5 « D - Initiations » (tables `plugin_pos_*` de
  l'extension Caisse).
- TiBillet : aucun accès à l'API ; l'Export des tickets est envoyé par
  l'utilisateur et n'est pas enregistré sur le disque.
- CSV du rapprochement : UTF-8, séparateur virgule, chaque valeur entre
  guillemets, fins de ligne CRLF.
