# Opérations

## Lire les initiations

Remplace la Lecture des initiations gardée en mémoire par une nouvelle
lecture.

HTTP : `GET /initiations/lecture`, réponse Datastar qui remplace le
contenu de la Page des initiations.

- [ok] L'API répond : la Lecture des initiations est remplacée ; la
  réponse affiche les Statistiques des initiations.
- [failed] Configuration absente, identifiants refusés, API
  injoignable ou toute autre réponse : refusé, avec le message du cas
  correspondant de /operations/tester-la-connexion ; la Lecture des
  initiations gardée en mémoire ne change pas.
