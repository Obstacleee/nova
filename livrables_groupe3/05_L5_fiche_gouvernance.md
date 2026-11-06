# Fiche de gouvernance · référentiel Client · Groupe 3

## Périmètre et définition
Le **référentiel client** désigne l'ensemble des attributs décrivant une personne qui achète chez NovaCommerce : identité, coordonnées, adresse de livraison et de facturation, statut, consentement marketing. Il est aujourd'hui éclaté en **trois copies** : CRM (15 412 lignes, 15 352 identifiants distincts), ERP de facturation (11 805 lignes) et fiches créées en caisse (312 identifiants « B- »).

**Constats chiffrés (mission 7)**
- Lien ERP → CRM : **249 `client_crm_id` vides** (dont 100 clients créés directement dans l'ERP avec un identifiant « E… » et 149 sans raison apparente) et **80 inconnus** du CRM ; 52 liens pointent vers un identifiant CRM dupliqué (donc ambigu).
- Sur les **11 424 liens valides** (clés CRM uniques) : **236 e-mails divergents** (sur 11 118 comparables), **579 adresses**, **524 codes postaux** et **498 villes** différents. Pourtant `date_maj` est **identique dans 11 423 cas sur 11 424** : la date ne permet pas de dire quelle version est la plus récente, ce qui interdit une règle « dernière mise à jour gagne ».
- 3 868 clients CRM n'ont aucune fiche ERP (non facturés ou lien manquant).
- **Nadia Benali (C1042)** : CRM fiche C1042 (Toulouse, 12 rue des Lilas, WEB, `date_maj` 30/10/2026), ERP fiche C1042 « N. Benali » (Blagnac, 4 avenue d'Andromède, 31700, `date_maj` 12/05/2026) : adresses différentes. Une 3e fiche **B-77810** (CAISSE, « BENALI », même e-mail `nadia.benali@example.com`, Toulouse, `date_maj` 12/07/2026). Sa commande CMD25001 est facturée deux fois.
- **Fiches B-** : 312 fiches créées en caisse (canal CAISSE, aucun client_id « C »), **305 ont un e-mail identique à une fiche « C… »** et 156 le même nom et prénom : elles viennent du flux L02 « création de fiche client à chaque vente » sans recherche préalable (hypothèse : c'est l'origine des 312 clients facturés deux fois de l'incident de mars, à valider). Aucune commande du JSON ne référence une fiche B-.

## Applications et processus (matrice CRUD actuelle et cible)
Voir `05_L5_matrice_crud.csv` (reconstituée à partir du dossier et de `flux_lineage.csv` ; **à valider avec les propriétaires d'application**). **Ce qu'elle révèle sur l'origine des doublons** : la fiche client est créée (C) par quatre applications (site, caisse, CRM, ERP) sans identifiant partagé ni contrôle d'existence ; modifiée (U) dans le CRM et l'ERP indépendamment ; personne n'a le droit d'écriture exclusif. Cible : création et fusion uniquement via un service de référentiel (MDM) par le Data Steward ; les autres applications lisent (R) ou proposent une création via l'API.

## Source qui fait foi, attribut par attribut
| Attribut | Source qui fait foi | Règle de survie | Justification |
|---|---|---|---|
| Identifiant client | CRM (futur MDM) | Le plus ancien `client_id` « C… » survit; l'ID absorbé reste en table d'alias | Stabilité des références (commandes, factures) |
| Adresse de livraison | CRM | Dernière adresse **confirmée par le client** (web ou service client) | Le CRM est alimenté par le client; incident des 47 colis |
| Adresse de facturation | ERP | Adresse portée sur la dernière facture émise, historisée | Valeur légale de la facture |
| E-mail | CRM | E-mail vérifié (lien de confirmation) le plus récent; jamais fusionné sur le seul e-mail | L'e-mail ne prouve pas l'identité |
| Consentement marketing | CRM (point unique) | Le **refus** l'emporte; horodaté avec la preuve | RGPD : preuve du consentement |
| Statut (ACTIF/INACTIF) | CRM | Calculé : ACTIF si commande dans les 12 mois, sinon INACTIF | Éviter la saisie libre (SUSPENDU, ACT) |

## Règles de création et de modification
- **Création** : recherche préalable obligatoire (e-mail normalisé, nom + prénom + code postal, téléphone) avant toute création; la caisse n'écrit plus dans le CRM, elle appelle l'API de référentiel.
- **Identifiant** : séquence unique centralisée, jamais réutilisée (60 collisions constatées); les fiches « B- » sont migrées vers « C… ».
- **Modification** : champs contrôlés (e-mail, code postal à 5 chiffres, téléphone à 10 chiffres, date ISO 8601, `date_maj` >= `date_creation`); historisation de l'adresse (voir ci-dessous).
- **Adresse historisée** : table `adresse_client(client_id, adresse, code_postal, ville, date_debut, date_fin)`; le changement ferme la ligne précédente (`date_fin`) plutôt que d'écraser; la livraison utilise la ligne valide à la date d'expédition.

## Règles de rapprochement et de survie (procédure en six étapes)
1. **Normaliser** : minuscules, sans accents ni espaces, téléphone en 10 chiffres, code postal sur 5 caractères, e-mail nettoyé.
2. **Générer des paires candidates (blocage)** : même nom + prénom normalisés. Sur le CRM, cela donne **82 692 paires**, dont l'immense majorité sont des homonymes (jeu synthétique avec 80 prénoms × 228 noms).
3. **Comparer** : date de naissance, e-mail, téléphone, code postal.
4. **Scorer** : date de naissance identique = 2, e-mail identique = 2, téléphone identique = 1, code postal identique = 1.
5. **Décider** : score >= 3 → fusion proposée (**219 paires**); score 2 → revue humaine (**7 paires**); score <= 1 → homonymes, pas de fusion (**82 466 paires**). Aucune fusion automatique pour les clients ayant des factures.
6. **Tracer** : table des décisions (paires, score, décideur, date), alias des identifiants absorbés, possibilité d'annuler.

La règle « même nom et prénom seuls » proposerait 82 692 fusions, dont plus de 99,7 % erronées (homonymes) : elle est à proscrire. L'e-mail seul est insuffisant (340 e-mails sont partagés par plusieurs identifiants).

## Responsables (Data Owner, Data Steward, IT, métier)
| Rôle | Titulaire proposé | Responsabilité |
|---|---|---|
| Data Owner référentiel client | Direction commerciale | Définit les règles, arbitre les fusions et la source qui fait foi |
| Data Steward | Responsable relation client (1 personne + suppléant) | Applique les règles, traite les paires à revoir, suit l'indicateur |
| IT | IT Data + IT magasins | Met en œuvre l'API de référentiel, la séquence d'ID, les contrôles à la création |
| Métier | Finance (facturation), Logistique (adresses), DPO (consentement, exactitude) | Valident les règles de leur périmètre |

## Procédure de résolution des conflits
**Prévention CRM / facturation** : l'ERP ne crée plus de client (les 100 fiches « E… » sont régularisées) ; toute modification d'adresse ou d'e-mail se fait dans le référentiel puis se propage à l'ERP; une modification faite dans l'ERP crée une demande de mise à jour, pas d'écrasement. **Si conflit détecté** (e-mail ou adresse différents entre CRM et ERP, comme les 236 et 579 cas) : (1) comparer les dates réelles de modification (à enregistrer, car `date_maj` est identique dans 99,99 % des cas) ; (2) appliquer la table « source qui fait foi » ; (3) en cas de doute, demande de confirmation au client ; (4) décision et motif tracés par le Data Steward ; délai de traitement de 5 jours ouvrés.

## Indicateur de suivi
- **Taux de fiches client uniques** = identifiants uniques ÷ lignes CRM (aujourd'hui 15 352 / 15 412 = 99,6 %), cible 100 %.
- **Taux de liens ERP → CRM valides** = liens valides ÷ lignes ERP (aujourd'hui 11 424 / 11 805 = 96,8 %), cible >= 99 %.
- **Taux d'adresses concordantes CRM/ERP** = 1 − 579 / 11 424 = 94,9 %, cible >= 98 %.
- Suivi mensuel par le Data Steward, remonté au comité de pilotage des données.
