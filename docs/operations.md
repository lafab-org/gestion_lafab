# Opérations

## Tester la connexion

Vérifie que l'API Paheko répond aux identifiants configurés.

HTTP : `GET /connexion`, réponse Datastar qui remplace l'état de
connexion de la page.

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
