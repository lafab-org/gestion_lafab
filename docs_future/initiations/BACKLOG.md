# Initiations

Suivi des initiations de l'atelier, enregistrées par les formateurs
dans Paheko : statistiques mensuelles par catégorie, puis rapprochement
avec les ventes.

## Outline

1. Rapprochement : /model/categorie-dinitiation, /model/initiation,
   /model/membre, /model/billet, /model/ligne-de-caisse,
   /model/mot-cle-dactivite, /model/vente-dinitiation,
   /model/export-des-tickets, /model/rapprochement-des-initiations,
   /operations/rapprocher-les-initiations,
   /operations/telecharger-le-rapprochement, /ui/page-des-initiations,
   /ui/page-du-rapprochement-des-initiations, /technical/pile,
   /scenarios/preparer-limport-des-initiations.

## Lessons

- Le Rapprochement a besoin de sa propre requête Paheko, avec membre et
  activité : celle des initiations ne lit que `id_service` et `date`.
- Le Paheko simulé de `tests/fakes.py` a déjà les activités 20 à 35 par
  catégorie et des activités hors initiation, réutilisables.

## For the human

- `app.py` répète par page la paire de routes page + lecture et sa
  mémoire : à factoriser à la troisième page.
- `charts.py` mêle graphiques des adhésions et des initiations : à
  séparer si d'autres graphiques arrivent.
- `run_sql` n'a pas de paramètres liés : les requêtes sont des f-strings
  de constantes pour l'instant.
