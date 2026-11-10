# Opérations

## Tester la connexion

Vérifie que l'API Paheko répond aux identifiants configurés.

HTTP : `GET /connexion`, réponse Datastar qui remplace le statut
de connexion de la page.

- [config] Une variable de configuration absente ou vide : refusé,
  `Configuration manquante : <variables>.`, les variables manquantes
  séparées par des virgules, dans l'ordre de /technical/lancement-et-configuration.
- [ok] L'API accepte les identifiants : `Connecté à <url>.`
- [refused] L'API refuse les identifiants : refusé,
  `Identifiants refusés par <url>.`
- [unreachable] L'API ne répond pas (réseau, nom inconnu, délai
  dépassé) : refusé, `Impossible de joindre <url>.`
- [unexpected] Toute autre réponse : refusé,
  `Réponse inattendue de <url> : code <code HTTP>.`

## Lire les adhésions

Remplace la Lecture Paheko gardée en mémoire par une nouvelle lecture.

HTTP : `GET /adhesions/lecture`, réponse Datastar qui remplace le
contenu de la Page des adhésions.

- [ok] L'API répond : la Lecture Paheko est remplacée.
- [failed] Configuration absente, identifiants refusés, API
  injoignable ou toute autre réponse : refusé, avec le message du cas
  correspondant de /operations/tester-la-connexion ; la Lecture Paheko
  gardée en mémoire ne change pas.
