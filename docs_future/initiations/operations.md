# Opérations

## Lire les initiations

Remplace la Lecture des initiations gardée en mémoire par une nouvelle
lecture.

HTTP : `GET /initiations/lecture`, réponse Datastar qui remplace le
contenu de la Page des initiations.

- [ok] L'API répond : la Lecture des initiations est remplacée.
- [failed] Configuration absente, identifiants refusés, API
  injoignable ou toute autre réponse : refusé, avec le message du cas
  correspondant de /operations/tester-la-connexion ; la Lecture des
  initiations gardée en mémoire ne change pas.

## Rapprocher les initiations

Remplace le Rapprochement des initiations gardé en mémoire par celui du
mois et de l'Export des tickets envoyés.

HTTP : `POST /initiations/rapprochement`, avec le mois et le fichier ;
réponse Datastar qui remplace le résultat sur la Page du rapprochement
des initiations.

- [ok] Export des tickets lisible ou aucun fichier envoyé, Paheko
  répond : le Rapprochement des initiations est remplacé par celui du
  mois. Ses lignes :
  - [billet] une vente par Billet de l'export dont `produit` commence
    par `Initiation` et `date` est dans le mois : `libelle` son
    `evenement`, `date` sa `date`, `email` son `email`, `membre` le
    Membre de même `email` ;
    - [membre-vide] aucun membre, ou plusieurs, avec cet e-mail :
      `membre` vide ;
  - [caisse] une vente par Ligne de caisse de `categorie`
    « D - Initiations » et d'`ouverture` dans le mois : `libelle`,
    `membre` et `nom` les siens, `date` son `ouverture` ;
    - [quantite] une ligne de `quantite` `q` supérieure à 1 donne `q`
      ventes : la première avec le membre de la note, les autres sans
      membre ; toutes avec la remarque
      `Quantité <q>, payée par <nom>.` ;
  - [nofile] aucun fichier envoyé : seulement les ventes de la caisse ;
  - [activite] `activite` : l'activité dont un Mot-clé d'activité est
    dans `libelle`, sans tenir compte de la casse ni des accents ;
    - [activite-vide] aucun mot-clé, ou des mots-clés de plusieurs
      activités : `activite` vide ;
  - [deja-inscrit] sans les ventes, avec membre et activité, dont le
    membre a déjà une Initiation de cette activité à la même date ;
  - [ordre] triées par date, puis par nom de membre, les ventes sans
    membre en dernier, puis par libellé.
- [export] Fichier envoyé qui n'est pas du JSON, ou billet sans l'un
  des champs de /model/billet : refusé,
  `Export des tickets illisible.` ; le rapprochement gardé en mémoire
  ne change pas.
- [failed] Export des tickets lisible ou aucun fichier envoyé, mais
  Paheko en échec (configuration absente, identifiants refusés, API
  injoignable ou toute autre réponse) : refusé,
  avec le message du cas correspondant de
  /operations/tester-la-connexion ; le rapprochement gardé en mémoire
  ne change pas.

## Télécharger le rapprochement

HTTP : `GET /initiations/rapprochement.csv`.

- [csv] Un rapprochement en mémoire : un fichier CSV
  `rapprochement-initiations-<AAAA>-<MM>.csv`, une ligne d'en-tête puis
  une ligne par ligne du rapprochement, dans son ordre, avec les
  colonnes :
  - `Numéro de membre` : le numéro du membre, vide sans membre ;
  - `Membre` : son nom et prénom ; sans membre, le nom de la note de
    caisse, vide pour un billet ;
  - `Activité` : le libellé Paheko de l'activité, vide sans activité ;
  - `Date d'inscription` : la date, `JJ/MM/AAAA` ;
  - `Payé ?` : `Oui` ;
  - `Source`, `E-mail`, `Libellé`, `Remarque`.
- [none] Aucun rapprochement en mémoire : réponse 404.
