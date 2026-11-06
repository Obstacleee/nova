# Dossier d'assurance qualité · projet décisionnel NovaCommerce · Groupe 3

*Missions 8 et 9. Chiffres arrêtés au 31/10/2026, reproductibles avec `code/m789.py`, `code/m9.py` et `code/m9b.py`.*

## 1. Périmètre, sources et données critiques (L1)
Dix sources (tabulaires, JSON, XML, logs, IoT, GPS, PDF, texte) et 13 données critiques classées par criticité (impact × exposition) : paiement (12), statut de commande (12), température (8), TTC/TVA de facture (8), e-mail et consentement (8), avis (8). Détail : `01_L1_matrice_donnees_critiques.csv`.

## 2. Résultats de l'audit (L2)
Conformité par règle : R01 91,57 %, R02 99,22 %, R03 98,87 %, R04 98,56 %, R05 97,17 %, R06 99,97 %, R07 99,57 %, R08 98,17 %, R09 88,11 %, R10 99,50 %. Aucun seuil à 100 % n'est atteint. Constat majeur : rupture de contrat de l'API commandes (schéma 2.0 depuis le 01/10). Détail : `02_L2_rapport_audit.md`.

## 3. Actions en cours et risques résiduels (L3)
Neuf anomalies traitées (5 en P1). **Risques résiduels** tant que les actions ne sont pas validées : indicateurs de CA non réconciliés; 310 doubles factures non régularisées; preuve de chaîne du froid incomplète pour le 14/10; données personnelles dans les avis. Détail : `03_L3_plan_remediation.csv`.

## 4. Règles, registre, lineage, journalisation (L4)
Douze règles (dont au moins sept hors tableaux), catalogue de 47 champs, registre de 6 données avec colonnes de souveraineté, deux lineages (CA et IoT) confrontés aux observations; **les journaux montrent qu'un statut SUCCES ne garantit pas la complétude** (792 mesures au lieu de 864 le 14/10). Détail : `04_L4_*`.

## 5. Référentiels et règles de gestion (L5)
Le référentiel client est éclaté en trois copies; `date_maj` identique dans 11 423 liens sur 11 424, donc inutilisable pour arbitrer; 312 fiches « B- » issues de la caisse (305 avec un e-mail déjà présent). Règle de rapprochement en six étapes (219 paires à fusionner, 7 à revoir, 82 466 homonymes écartés). Détail : `05_L5_fiche_gouvernance.md`.

## 6. Fiches indicateurs : CA mensuel, clients actifs, conformité de la chaîne du froid

### 6.1 Pourquoi aucun des cinq indicateurs publiés ne peut l'être tel quel
| Indicateur publié | Valeur | Pourquoi il ne peut pas être publié |
|---|---|---|
| CA_octobre_tableau_A (Direction commerciale) | 568 367,00 € | Somme des TTC *bruts* du JSON : inclut 14 messages en double, les commandes annulées (211) et non payées, trois valeurs aberrantes (48 216 € pour une commande de 419 € HT ; 11 925 € ; 6 232 €), des montants à virgule décimale (50) lus comme vides; le TTC n'est pas un chiffre d'affaires. |
| CA_octobre_tableau_B (Finance) | 438 457,68 € | Paiements acceptés ÷ 1,2 : la TVA moyenne n'est pas de 20 % (taux de 5,5 % et 20 % mélangés); inclut les événements en double et ignore les remboursements (38 977 € en octobre); rattache par la date du paiement, pas de la commande; 6 montants vides. |
| CA_octobre_jointure_commandes_paiements | 685 936,80 € | Jointure 1:N : une commande est répétée autant de fois qu'elle a d'événements de paiement (voir 6.3). |
| clients_actifs_12_mois | 11 429 | Nous retrouvons exactement 11 429 en comptant les `client_id` distincts **sur toute la période** : ni filtre de 12 mois, ni alias `customerId`, ni contrôle d'existence, ni statut de commande. |
| taux_conformite_chaine_du_froid_octobre_pct | 99,53 % | Retrouvé exactement : part des 26 788 lignes entre 0 et 4 °C. Les 50 mesures en °F sont comptées à tort non conformes; les doublons, les vides, les valeurs figées et le trou de 72 mesures ne sont pas traités. |

### 6.2 Fiche indicateur · Chiffre d'affaires d'octobre 2026
| Champ | Définition retenue |
|---|---|
| Définition | Montant **hors taxes** des commandes d'octobre 2026 passées et payées, hors annulations |
| HT ou TTC | **HT** (le TTC contient la TVA, qui appartient à l'État); TTC publié à côté, à titre d'information |
| Date de rattachement | `date_commande`, convertie en heure de Paris (Europe/Paris) : du 01/10 00:00 au 31/10 23:59 |
| Statuts inclus | PAYEE, EXPEDIEE, LIVREE (les statuts « LIVRER » et « livrée » sont normalisés en LIVREE). Exclus : ANNULEE, CREEE, vide |
| Remboursements | Déduits sur le mois de la date de remboursement; affichés sur une ligne séparée (38 977 € d'événements REFUND en octobre) |
| Doublons | Une seule occurrence par `commande_id` (2 739 commandes uniques sur 2 753 messages); les 20 identifiants à contenu contradictoire sont traités en revue |
| Fuseau | Europe/Paris; événements de paiement en UTC (Z) |
| Calcul | HT recalculé = Σ quantité × prix_unitaire_ht des lignes (les montants JSON incohérents ne sont pas utilisés) |
| Numérateur / dénominateur | Somme en euros; 2 439 commandes retenues sur 2 739 uniques d'octobre (PAYEE 273 + EXPEDIEE 268 + LIVREE 1 881 + LIVRER 15 + livrée 2) |
| Responsable / fréquence | Contrôle de gestion; quotidienne, figée au 5 du mois suivant |

**Résultat recalculé : CA HT d'octobre = 396 250,59 €** (commandes uniques, statuts PAYEE + EXPEDIEE + LIVREE, HT recalculé depuis les lignes). Avec les HT du JSON non recalculés : 397 207,54 € (écart de 957 € dû à 9 commandes dont le total ne correspond pas aux lignes).

**Comparaison avec A et B (pont indicatif)**
| Étape | Montant |
|---|---|
| Tableau A publié (TTC brut) | 568 367,00 € |
| A reproduit (TTC, heure de Paris, virgules corrigées) | 566 733,79 € (écart de 1 633 € = 0,29 %, cause non établie) |
| − doublons de messages (14) | 564 030,95 € |
| − commandes annulées, non payées ou sans statut | 507 703,96 € (TTC retenus) |
| − TVA et aberrations (passage au HT recalculé depuis les lignes) | **396 250,59 € HT** |
| Tableau B publié | 438 457,68 € |
| B reproduit (acceptés ÷ 1,2, UTC / heure de Paris) | 440 255,08 € / 441 114,61 € (écart de 0,4 à 0,6 %, non établi) |
| Paiements nets (acceptés dédoublonnés − remboursements) | 484 985,69 € TTC |

Les écarts entre A, B et notre chiffre s'expliquent par la définition (TTC contre HT), les statuts, les doublons, la date de rattachement et les remboursements, pas par une erreur de calcul unique.

### 6.3 Démonstration : la jointure commandes × paiements multiplie les montants
`controle_jointure(commandes d'octobre, paiements d'octobre, 'commande_id')` renvoie une **cardinalité 1:N** (max 1 à gauche, 3 à droite) : **2 739 lignes à gauche → 2 961 après jointure** (+8,1 %), parce que 315 commandes ont plusieurs événements (refus puis acceptation, remboursement). La somme des TTC passe de **564 030,95 € à 611 029,87 € (+46 998,92 €, +8,3 %)**. En joignant les commandes d'octobre à *tous* les événements de paiement, on obtient 684 093 € (publié : 685 936,80 €, écart de 0,27 % non établi). Règle : agréger les paiements **par commande** avant de joindre.

### 6.4 Fiche indicateur · Clients actifs sur 12 mois
Définition : nombre de clients **distincts et connus du CRM** ayant au moins une commande **payée** (PAYEE, EXPEDIEE, LIVREE) dans les 12 mois précédant le 01/11/2026; identifiant lu dans `client_id` ou `customerId`. Résultat recalculé : **11 130** (publié : 11 429, soit -299 ou -2,6 %). Écarts expliqués : commandes annulées ou non payées incluses dans le publié, clients inconnus du CRM (146 identifiants), alias `customerId` ignoré (qui ajoute 427 clients). **Réserve** : le fichier ne couvre que janvier à octobre 2026 (10 mois, pas 12) et 51 clients actifs ont un identifiant dupliqué dans le CRM.

### 6.5 Fiche indicateur · Conformité de la chaîne du froid (octobre)
Définition : part des mesures valides (unité °C, après conversion des °F, sans doublon, sans valeur aberrante) comprises entre 0 et 4 °C. Complétude suivie à côté. Résultat recalculé : **99,81 %** (sur 26 686 mesures valides après conversion des °F, retrait des doublons, des vides et des valeurs aberrantes); **99,45 %** si l'on rapporte les mesures conformes aux 26 784 mesures attendues (3 capteurs × 31 jours × 288), donc en comptant le trou comme non conforme. 50 mesures valides hors plage (6,0 à 7,5 °C), réparties sur CF-01 (18), CF-02 (12), CF-03 (20). Écart avec le publié (99,53 %) : +0,28 point, dû aux °F convertis et aux lignes invalides retirées; mais **le trou du 14/10 reste non prouvé**. Cas légitime : les 72 doublons du 25/10 (changement d'heure).

## 7. Critères d'intégration par source
| Source | Critère d'entrée dans l'entrepôt | Traitement |
|---|---|---|
| commandes_api.json | schema_version connu; `client_id` ou `customerId` présent; `commande_id` unique | alias, dédoublonnage, quarantaine des 20 conflits |
| paiements.log | `event_id` unique; UTC; montant renseigné | dédoublonnage, conversion UTC, quarantaine des vides |
| factures.xml | R03 + R09 | quarantaine des factures en écart |
| capteurs_froid.csv | 864 mesures/jour; °C; valeur présente | rejet du lot si volume < attendu; conversion des °F |
| clients_crm.csv | R02; formats; référentiels | normalisation tracée |
| livraisons_gps.csv | R07 | marquer les (0,0) comme inconnus |
| avis, PDF | R04, R08 | non intégrés à la BI tant que non conformes |

## 8. Contrôles de transformation et de réconciliation
1. **Clés** : unicité de `commande_id`, `event_id`, `numero` avant toute jointure.
2. **Cardinalité** : refuser une jointure dont le nombre de lignes dépasse celui de la table de gauche.
3. **Réconciliation des totaux** : CA HT de la BI = somme des factures HT du mois (à 0,5 % près); paiements nets ≈ TTC des commandes payées.
4. **Fraîcheur** : dernier événement reçu < 15 min (PSP), dernière mesure IoT < 15 min, API < 1 h.
5. **Journalisation** : chaque publication enregistre version de la règle, volumes entrée/chargé/rejeté et auteur.
6. **Volume** : écart à la moyenne des 7 jours précédents.

## 9. Décision de publication par indicateur
| Indicateur | Décision | Motif | Condition de levée |
|---|---|---|---|
| CA octobre · tableau A | **Suspendu** | TTC brut, doublons, annulées, aberrations | Remplacé par le CA HT recalculé (396 250,59 €) |
| CA octobre · tableau B | **Suspendu** | Division par 1,2 fausse, doublons, remboursements ignorés | Remplacé par le CA HT recalculé |
| CA octobre · jointure | **Suspendu** (requête ad hoc, jamais publiable) | Multiplication par la relation 1:N (+8,3 %) | Agrégation des paiements avant jointure |
| Clients actifs 12 mois | **Publié avec réserve** : 11 130, avec mention « 10 mois de données » | Définition corrigée, couverture incomplète | Historique complet de 12 mois et ID dédoublonnés |
| Conformité chaîne du froid | **Publié avec réserve** : 99,81 % avec mention du trou de 6 h le 14/10 | Indicateur sûr pour les mesures reçues, mais trou non prouvé | Récupération des mesures du 14/10 ou procès-verbal de la qualité |
| CA octobre · nouvelle fiche (HT) | **Publié avec réserve** | 20 identifiants contradictoires et 9 totaux incohérents en revue | Arbitrage Finance sur les 20 conflits |

## 10. Note de passage vers DATE733
- **Sources utilisables** : produits (après normalisation des catégories et de la TVA), commandes dédoublonnées avec alias de schéma, paiements dédoublonnés en UTC, factures après contrôle R03 et R09, capteurs nettoyés.
- **Sources à ne pas exploiter en BI pour l'instant** : avis (données personnelles), PDF (index non fiable), GPS (précision et inversions).
- **Transformations nécessaires** : alias `customerId` → `client_id`; `total_ttc` → `montant_total_ttc`; normalisation des statuts et casse; conversion UTC; °F → °C; agrégation des paiements par commande; recalcul du HT depuis les lignes.
- **Indicateurs proposés** : CA HT mensuel, clients actifs 12 mois, conformité chaîne du froid et complétude, taux de factures uniques, taux de commandes avec client connu.
- **Risques résiduels** : 20 conflits de statuts à arbitrer; 8 mois d'historique de factures manquants (factures sept.-oct. seulement); écarts de reproduction de A et B non expliqués; journal non rapprochable du JSON.
- **Prérequis avant production** : contrat d'interface signé et versionné; Data Owner nommé par flux; tests de réconciliation automatisés; registre de souveraineté confirmé par l'IT et le DPO.

---

## Annexe · Contrat d'interface de l'API commandes (mission 8)

### A. Dérive de schéma constatée
- Le **premier message en schéma 2.0 date du 01/10/2026 à 00:15** (heure de Paris); aucun en septembre. Sur octobre : 2 010 messages en 2.0 contre 743 en 1.0 (73 %), avec une proportion stable de 62 à 84 % par jour : bascule brutale, pas progressive.
- **Champs renommés** : `client_id` → `customerId` ; `montant_total_ttc` → `total_ttc`. **Champ vidé** : `contact.telephone` (nul dans 100 % des messages des deux versions). Absent en 2.0 : `client_id`, `montant_total_ttc`.
- **Contrôles et indicateurs faussés sans prévenir** : R01 (91,6 %), clients actifs (sous-estimés de 427 clients), rapprochement commande ↔ client pour la facturation, taux de rejet du journal (de 0-3 à 60-107 lignes par jour à partir du 15/10), CA par client.

### B. Contrat d'interface (version 2.1 proposée)
| Champ | Type | Obligatoire | Valeurs / format | Remarque |
|---|---|---|---|---|
| commande_id | texte | oui | `CMD` + entier, unique | Un identifiant n'est jamais réutilisé |
| schema_version | texte | oui | `MAJEUR.MINEUR` | Voir versionnement |
| client_id | texte | oui | `C` + entier existant dans le référentiel | Nom du champ **figé**; `customerId` déprécié |
| canal | texte | oui | WEB, CAISSE, B2B | B2B à ajouter au référentiel (20 cas observés) |
| date_commande | date-heure | oui | ISO 8601 avec fuseau (`2026-10-03T17:06:40+02:00`); jamais dans le futur | 100 dates au format JJ/MM/AAAA observées |
| statut | texte | oui | CREEE, PAYEE, EXPEDIEE, LIVREE, ANNULEE | Pas de casse libre (LIVRER, livrée observés) |
| lignes[].produit_id | texte | oui | `PR` + 4 chiffres existant dans produits | 81 inconnus observés |
| lignes[].quantite | entier | oui | > 0 | 80 <= 0 observés |
| lignes[].prix_unitaire_ht | décimal | oui | > 0, point décimal, 2 décimales | 562 à 0 observés |
| montant_total_ht | décimal | oui | = Σ quantité × prix (0,01 €) | 185 écarts |
| montant_total_ttc | décimal | oui | nombre JSON (pas de texte, pas de virgule); nom figé | `total_ttc` déprécié |
| contact.email | texte | non | nom@domaine.tld | 184 invalides |
| contact.telephone | texte | non | 10 chiffres | toujours vide aujourd'hui |

### C. Versionnement, prévenance et engagements
- **Versionnement** : MAJEUR change = renommage, suppression ou changement de type; MINEUR = ajout de champ optionnel. Le fournisseur ne supprime ni ne renomme un champ dans une version existante.
- **Délai de prévenance** : 30 jours avant tout changement MAJEUR, avec coexistence des deux versions pendant 60 jours, annonce écrite au Data Owner et à l'IT Data.
- **Fraîcheur** : 99 % des commandes disponibles en moins de 5 minutes; **volume** : alerte si le volume quotidien s'écarte de plus de 30 % de la moyenne des 7 jours précédents (ou panne confirmée); **qualité** : au moins 99 % de messages conformes au contrat, rejet motivé pour les autres.

### D. Moniteurs d'observabilité (cinq familles, six mesures) (seuils calculés sur les données)
| Moniteur | Mesure | Seuil | Valeur normale observée | Résultat sur octobre |
|---|---|---|---|---|
| Fraîcheur | Écart entre `recu` et `event_time` du PSP | alerte à 15 min | médiane 45 s; p95 86 s; p99 90 s | 30 événements > 1 h |
| Volume | Commandes par jour vs moyenne J-7 | ±30 % | écart maximum observé : -22,6 % (27/10) et +23,1 % (28/10) | **jamais déclenché** |
| Volume capteurs | Mesures par jour | < 864 | 864 | **14/10 : 792 (-8,3 %)** |
| Schéma | Part de commandes sans `client_id` par jour | > 5 % | 0 % de janvier à septembre | **01/10 : 62 à 84 % par jour** |
| Distribution | Taux de rejet de l'import commandes | > 1 % | 0 à 0,9 % avant le 15/10 | 8 à 27 % à partir du 15/10 (hors run de 10 000 lignes) |
| Lineage | Lignes après jointure ÷ lignes avant | > 1,00 | 1,00 | 1,081 (2 961 / 2 739) |

### E. Quel moniteur aurait détecté l'incident le plus tôt ?
- **Moniteur de schéma** : alerte dès le **01/10/2026** (premières heures), soit **14 jours avant** le premier ECHEC_SEUIL du pipeline (15/10).
- **Moniteur de volume des commandes** : n'aurait **jamais** alerté (volume stable à ±23 %) : un volume correct n'implique pas un contenu correct.
- **Moniteur de volume des capteurs** : aurait alerté le **14/10/2026** (792 lignes au lieu de 864), le jour même du trou de 6 h, alors que le journal affichait SUCCES.
