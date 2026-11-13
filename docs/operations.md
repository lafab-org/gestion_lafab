# Opérations

## État initial

Trigger: le lancement de l'application.

- [vide] Aucune Lecture Paheko, aucune Lecture des initiations, aucun
  Rapprochement des initiations.

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

- [ok] L'API accepte les identifiants et renvoie le résultat de la
  requête : la Lecture Paheko est remplacée.
- [failed] Configuration absente, identifiants refusés, API
  injoignable ou toute autre réponse : refusé, avec le message du cas
  correspondant de /operations/tester-la-connexion, celui de
  /operations/tester-la-connexion/unexpected pour une réponse qui
  accepte les identifiants sans résultat lisible ; la Lecture Paheko
  gardée en mémoire ne change pas.

## Lire les initiations

Remplace la Lecture des initiations gardée en mémoire par une nouvelle
lecture.

HTTP : `GET /initiations/lecture`, réponse Datastar qui remplace le
contenu de la Page des initiations.

- [ok] L'API accepte les identifiants et renvoie le résultat de la
  requête : la Lecture des initiations est remplacée.
- [failed] Configuration absente, identifiants refusés, API
  injoignable ou toute autre réponse : refusé, avec le message du cas
  correspondant de /operations/tester-la-connexion, celui de
  /operations/tester-la-connexion/unexpected pour une réponse qui
  accepte les identifiants sans résultat lisible ; la Lecture des
  initiations gardée en mémoire ne change pas.

## Rapprocher les initiations

Remplace le Rapprochement des initiations gardé en mémoire par celui du
mois et de l'Export des tickets envoyés.

HTTP : `POST /initiations/rapprochement`, avec le mois et le fichier ;
réponse Datastar qui remplace le résultat sur la Page du rapprochement
des initiations.

Entrées :
- `mois` : le mois, `AAAA-MM`.
  - [mois-invalide] Absent, ou qui n'est pas un mois `AAAA-MM` : le
    mois précédent celui du jour.
- `fichier` : l'Export des tickets, ou aucun fichier.

Cas :

- [ok] Export des tickets lisible ou aucun fichier envoyé, l'API
  Paheko accepte les identifiants et renvoie le résultat des requêtes :
  le Rapprochement des initiations est remplacé par celui du
  mois. Ses lignes :
  - [billet] une vente par Billet de l'export dont `produit` commence
    par `Initiation` et `date` est dans le mois : `libelle` son
    `evenement`, `date` sa `date`, `email` son `email` sans espaces
    autour, `membre` le Membre de même `email`, sans tenir compte de la
    casse ni des espaces autour ;
    - [membre-vide] billet sans e-mail, ou aucun membre, ou plusieurs,
      avec cet e-mail : `membre` vide ;
  - [caisse] une vente par Ligne de caisse de `categorie`
    « D - Initiations » et d'`ouverture` dans le mois : `libelle`,
    `membre` et `nom` les siens, `date` son `ouverture` ;
    - [quantite-nulle] une ligne de `quantite` nulle ou négative : aucune
      vente ;
    - [quantite] une ligne de `quantite` `q` supérieure à 1 donne `q`
      ventes : la première avec le membre et le nom de la note, les
      autres sans membre ni nom ; toutes avec la remarque
      `Quantité <q>, payée par <nom>.`, `<nom>` le nom de la note ;
      - [sans-nom] note sans nom : la remarque `Quantité <q>.` ;
    - [remarque-vide] une ligne de `quantite` 1 : `remarque` vide ;
  - [remarque-billet] `remarque` vide pour un billet ;
  - [nofile] aucun fichier envoyé : seulement les ventes de la caisse ;
  - [activite] `activite` : l'activité dont un Mot-clé d'activité est
    dans `libelle`, sans tenir compte de la casse ni des accents ;
    - [activite-vide] aucun mot-clé, ou des mots-clés de plusieurs
      activités : `activite` vide ;
  - [deja-inscrit] sans les ventes, avec membre et activité, dont le
    membre a une Initiation de cette activité à la même date, lue dans
    Paheko au moment du rapprochement ;
  - [ordre] triées par date, puis par nom de membre sans tenir compte
    de la casse ni des accents, les ventes sans membre en dernier, puis
    par libellé, caractère par caractère ; l'ordre des ventes égales sur ces clés est libre ;
  - [libelles] `libelles` : les Libellés d'activité lus dans Paheko.
- [export] Fichier envoyé qui n'est pas une liste JSON de Billets :
  pas du JSON, pas une liste, un élément qui n'est pas un objet, un
  champ de /model/billet absent ou qui n'est pas un texte, ou un
  `event_datetime` qui n'est pas une date et une heure valides au
  format `JJ/MM/AAAA HH:MM` : refusé,
  `Export des tickets illisible.` ; le rapprochement gardé en mémoire
  ne change pas.
- [failed] Export des tickets lisible ou aucun fichier envoyé, mais
  Paheko en échec (configuration absente, identifiants refusés, API
  injoignable ou toute autre réponse) : refusé,
  avec le message du cas correspondant de
  /operations/tester-la-connexion, celui de
  /operations/tester-la-connexion/unexpected pour une réponse qui
  accepte les identifiants sans résultat lisible ; le rapprochement gardé en mémoire
  ne change pas.

## Télécharger le rapprochement

HTTP : `GET /initiations/rapprochement.csv`.

- [csv] Un rapprochement en mémoire : un fichier CSV
  `rapprochement-initiations-<AAAA>-<MM>.csv`, une ligne d'en-tête puis
  une ligne par ligne du rapprochement, dans son ordre, avec les
  colonnes :
  - `Numéro de membre` : le numéro du membre, vide sans membre ;
  - `Membre` : son nom et prénom ; sans membre, le `nom` de la vente ;
  - `Activité` : le Libellé d'activité de `libelles`, vide sans
    activité ou sans libellé lu ;
  - `Date d'inscription` : la date, `JJ/MM/AAAA` ;
  - `Payé ?` : `Oui` ;
  - `Source`, `E-mail`, `Libellé`, `Remarque`.
- [none] Aucun rapprochement en mémoire : réponse 404.
