# Rapport d'audit qualité · NovaCommerce · Groupe 3

*DATE732 · missions 2 à 4 · données synthétiques arrêtées au 31/10/2026 · tous les chiffres sont reproductibles avec `code/analyse_groupe3.py` et les scripts `code/m*.py`.*

## Synthèse pour la direction (une page)

**3 constats**
1. **Le contrat de l'API commandes a changé sans prévenir.** Depuis le 1er octobre 2026, 73 % des commandes (2 010 sur 2 753) arrivent en schéma 2.0 : `client_id` devient `customerId`, `montant_total_ttc` devient `total_ttc`. La règle R01 « chaque commande a un client connu » tombe à 91,6 %, alors que 93 % de cet écart vient du simple renommage du champ.
2. **Les contrôles existants ne protègent pas les flux critiques.** 310 commandes (620 factures) sont facturées deux fois ; un trou de 6 h dans la chambre froide CF-03 (14/10) est chargé avec le statut SUCCES ; 59 avis publiés exposent un e-mail ou un téléphone.
3. **Les trois chiffres d'affaires d'octobre sont faux ou non comparables** : 568 367 € (A), 438 458 € (B), 685 937 € (jointure) contre **396 251 € HT recalculé** (commandes uniques, statuts payée / expédiée / livrée, HT recalculé depuis les lignes).

**3 chiffres**
- **88,1 %** des factures sont conformes à R09 (une commande = une facture) : 620 factures sur 5 214 concernées.
- **8,4 %** des commandes ne se rattachent à aucun client dans le CRM (2 143 sur 25 422).
- **99,81 %** de conformité réelle de la chaîne du froid (après nettoyage), contre 99,53 % publié, mais avec **72 mesures manquantes en une seule fois**, donc non prouvable pendant 6 h.

**3 priorités (P1)**
1. Rétablir le contrat d'interface commandes (alias `customerId`, versionnement, moniteur de schéma) et rejouer les imports du 15 au 31/10.
2. Dépublier les 59 avis contenant des données personnelles et corriger les 310 doubles facturations (avoirs après arbitrage de la Finance).
3. Suspendre les trois indicateurs de CA et publier un chiffre unique, avec fiche indicateur.

---

## 1. Contexte et périmètre

NovaCommerce (épicerie fine en ligne, 12 boutiques, 2 entrepôts dont un frais) constate des écarts entre CRM, facturation, commandes, paiements, livraisons et tableaux de bord (incident de mars 2026 : 312 clients facturés deux fois, 47 colis mal adressés, deux chiffres d'affaires, 6 h sans mesure de froid). La direction demande : « Peut-on encore faire confiance à nos données ? »

**Périmètre** : les quatorze sources fournies dans `donnees/`, soit 15 412 fiches CRM, 11 805 clients ERP, 365 produits, 25 422 messages de commande (25 312 identifiants uniques), 5 214 factures XML (sept.-oct. 2026), 28 155 événements de paiement, 26 788 mesures de température (octobre), 14 982 livraisons, 5 194 PDF indexés, 4 100 avis. **Hors périmètre** : conformité réglementaire globale (nous proposons une démarche de mise en conformité sur ce périmètre, nous ne la démontrons pas).

## 2. Sources analysées et leur type

| Source | Type | Rôle | Volume |
|---|---|---|---|
| clients_crm.csv | Tabulaire | Fiches clients | 15 412 lignes |
| clients_facturation.csv | Tabulaire | Clients de l'ERP | 11 805 |
| produits.csv | Tabulaire | Référentiel produits | 365 |
| commandes_api.json | JSON imbriqué | Commandes site + caisses, 2 versions de schéma | 25 422 messages, 48 052 lignes |
| factures.xml | XML | Factures sept.-oct. 2026 | 5 214 |
| paiements.log | Logs | Événements du PSP (29 lignes WARN techniques exclues) | 28 155 |
| capteurs_froid.csv | Série temporelle | 3 chambres froides, 1 mesure / 5 min | 26 788 |
| livraisons_gps.csv | Géographique | Statut et GPS de livraison | 14 982 |
| factures_pdf_index.csv + échantillon | Documents | Index des PDF (11 fichiers dans l'échantillon) | 5 194 |
| avis_clients.csv | Texte libre | Avis publiés | 4 100 |

## 3. Dimensions et règles retenues (R01 à R08 + nos R09, R10)

Les sept dimensions du syllabus sont couvertes : exactitude (R03, R07, R10), complétude (R06), cohérence (R03, R05), unicité (R02, R05, R09), conformité (R04, R05), fraîcheur (R06) et intégrité (R01, R08).

| Règle | Énoncé | Dimension |
|---|---|---|
| R01 | Chaque commande référence un client existant dans le CRM | Intégrité |
| R02 | `client_id` unique dans le CRM | Unicité |
| R03 | TTC = HT + TVA à 0,01 € | Cohérence |
| R04 | Aucune donnée personnelle dans un avis publié | Conformité |
| R05 | `event_id` unique et horodatage en UTC | Unicité, conformité |
| R06 | Température entre -40 et +60 °C, une mesure / 5 min | Complétude, exactitude |
| R07 | Livraison dans la France métropolitaine | Exactitude |
| R08 | Chaque PDF est rattaché à une commande existante | Intégrité |
| **R09 (nouvelle)** | **Une commande n'est facturée qu'une fois** : périmètre `factures.xml`, condition `commande_id` unique parmi les factures, seuil 0 anomalie, action : bloquer la 2e émission puis avoir | Unicité |
| **R10 (nouvelle)** | **Capteur : unité °C, valeur présente, aucune valeur strictement constante sur 1 h** : périmètre `capteurs_froid.csv`, seuil 0, action : signaler le capteur et exclure du KPI | Exactitude |

R09 et R10 couvrent deux anomalies qu'aucune règle R01 à R08 ne détecte : la double facturation (les factures sont cohérentes entre elles, mais deux numéros existent pour une même commande) et les mesures de température aberrantes ou figées mais bien formées (R06 ne voit que la plage et le rythme).

## 4. Méthode : outils, échantillon, limites

- **Outils** : Python 3 / pandas, boîte à outils du notebook `audit_novacommerce.ipynb` (reprise dans `code/nv.py`). Toutes les sources sont lues **en texte** pour ne rien corriger sans le vouloir. Aucun fichier source n'a été modifié.
- **Pas d'échantillon** : toutes les lignes sont contrôlées.
- **Unités comptées** : chaque taux indique ce qui est compté (lignes ou clés) et son dénominateur ; un enregistrement peut porter plusieurs anomalies.
- **Hypothèse sur les dates sans fuseau** : supposées en UTC pour les comparaisons ; le mois d'octobre est borné en heure de Paris (Europe/Paris).
- **Limites** : voir section 9.

## 5. Résultats chiffrés par règle

| Règle | Unité comptée | Contrôlés | En anomalie | % conformes | Seuil | Conclusion |
|---|---|---|---|---|---|---|
| R01 | commandes (messages JSON) | 25 422 | 2 143 | **91,57** | >= 99 % | **Non conforme** (cause principale : contrat) |
| R02 | lignes CRM (60 clés distinctes) | 15 412 | 120 | 99,22 | 100 % | **Non conforme** (erreur certaine) |
| R03 | factures | 5 214 | 59 | 98,87 | 100 % | **Non conforme** (écart de 0,01 € à plusieurs euros) |
| R04 | avis publiés | 4 100 | 59 | 98,56 | 100 % | **Non conforme** (RGPD) |
| R05 | événements PSP | 28 155 | 797 | 97,17 | 100 % | **Non conforme** (500 lignes en double, 303 hors UTC) |
| R06 | mesures | 26 788 | 7 | 99,97 | >= 99,9 % | **À investiguer** (1 trou de 365 min, 6 valeurs hors plage : -200, -127, 85 °C) |
| R07 | livraisons | 14 982 | 65 | 99,57 | 100 % | **Non conforme** (40 inversées, 15 à 0,0) |
| R08 | PDF | 5 194 | 95 | 98,17 | 100 % | **Non conforme** |
| R09 | factures | 5 214 | 620 | **88,11** | 100 % | **Non conforme** (310 commandes) |
| R10 | mesures | 26 788 | 135 | 99,50 | 100 % | **À investiguer** (50 °F, 20 vides, 65 figées) |

*Justification des seuils* : 100 % pour les règles d'unicité et de conformité réglementaire (une seule faute suffit à créer un litige ou une fuite) ; 99 % pour R01 car un rejet résiduel de 1 % (1 à 3 rejets par jour observés avant le 15/10 dans `journaux_traitements.csv`) est le niveau « normal » de l'entreprise ; 99,9 % pour R06 car les capteurs peuvent perdre une mesure isolée.

### 5.1 Profilage et résultats détaillés de la mission 2

- **Schémas JSON** : version 1.0 = 23 412 messages, version 2.0 = 2 010 (tous en octobre). En 2.0, `client_id` et `montant_total_ttc` sont vides à 100 %, remplacés par `customerId` (renseigné à 1 985 / 2 010) et `total_ttc`. `contact.telephone` est vide à 100 % dans les deux versions. Le champ statut est vide dans 28 + 2 messages.
- **Unicité** (R02) : 120 lignes CRM portent un `client_id` dupliqué, soit **60 clés distinctes** ; chaque paire désigne deux personnes différentes (60 / 60 avec contenu différent). Commandes : **220 lignes pour 110 `commande_id` dupliqués** ; **90 doublons exacts** et **20 identifiants réutilisés avec un contenu différent** (statut ANNULEE contre LIVREE dans les cas examinés).
- **Référentiels** : statut client 76 valeurs hors référentiel après normalisation de la casse (SUSPENDU 39, ACT 37) et 170 sans normalisation ; pays 116 (France 42, FRA 38, F 36) ; statut de commande 189 (LIVRER 119, livrée 40, vide 30) ; catégorie produit 12 mal casées ; TVA : 3 produits à 19,6 % et **77 lignes de facture à 19,6 %** (taux supprimé).
- **Formats du CRM** (un format valide ne prouve pas l'exactitude) : e-mail 257 invalides (« camille@@example.com », espace) ; téléphone 260 (« +33 6… », 9 chiffres) ; code postal 145 à 4 chiffres (« 1000 », zéro initial perdu) ; date de création 243 non ISO (« 12/09/2021 »). 400 e-mails, 158 téléphones et 612 consentements sont vides.
- **Intégrité** : produits commandés inconnus **81 lignes sur 48 052** (PR5xxx, 77 produits) ; factures dont la commande est inconnue **25** ; clients de factures inconnus 28 et vides 46. Pour R01 (décomposition) : **25** commandes sans aucun identifiant, **1 985** avec l'identifiant sous le nom `customerId` (dont 16 inconnus du CRM) et **133** avec un `client_id` inconnu ; soit 92,6 % de l'écart dû au renommage.
- **Montants** : `montant_total_ht` différent de Σ quantité × prix dans **185 commandes uniques** (prix à 0 : 562 lignes ; quantité <= 0 : 80 ; 10 commandes > 5 000 € HT dont 22 381 €) ; `montant_total_ttc` non numérique dans 50 cas (virgule décimale : « 53,19 ») ; sur les factures, 59 écarts R03 et 36 TTC négatifs ou nuls ; 15 devises vides.
- **Dates** : `date_maj` antérieure à `date_creation` pour 88 clients ; 10 naissances dans le futur (jusqu'en 2027) et 25 clients de moins de 16 ans ; 15 commandes datées en 2027 (jusqu'au 17/10/2027) ; 20 factures émises avant leur commande ; 117 factures de novembre 2026 et 14 de 2027 (dont dates non ISO).

### 5.2 Résultats détaillés de la mission 3 (hors tableaux)

- **Logs** : 29 lignes WARN exclues du motif ; 28 155 événements, **250 `event_id` en double** (500 lignes, tous des doublons exacts) ; **60 montants vides** (tous PAYMENT_ACCEPTED) ; 51 événements de type `PAYMENT_VALIDATED`, absent du référentiel ; **122 événements sur 120 commandes inconnues**. Horloges : réception médiane à +45 s de `event_time` (p95 : 86 s), mais **303 `event_time` hors UTC** (+01:00 : 43, +02:00 : 114, sans fuseau : 146) et 30 événements reçus plus d'une heure après ; 146 `event_time` sans fuseau, lus comme de l'UTC, semblent postérieurs de 1 à 2 h à leur réception (heure locale probable). 15 événements ont une date en 2027.
- **Capteurs** : 50 mesures en °F (36,9 à 38,3 °F, soit 2,7 à 3,5 °C : des valeurs correctes dans une autre unité, comptées à tort hors 0-4 par le KPI publié) ; 20 températures vides ; 6 valeurs hors plage (-200 °C ×2, -127 °C ×2, 85 °C ×2) ; **1 trou de 365 min** sur CF-03 le 14/10 à 07:00 (~72 mesures manquantes, le « 6 heures » de l'incident) ; **152 lignes à horodatage dupliqué** : 72 le 25/10 entre 02:00 et 02:55 (3 capteurs × 12 pas × 2) = **cas légitime**, c'est le retour à l'heure d'hiver ; les 80 autres, réparties sur d'autres jours, sont des doublons de collecte (100 lignes sont identiques en tout point) ; 65 mesures figées sur 1 h (CF-02, du 03 au 06/10, CF-01 et CF-03 ponctuellement).
- **GPS** : 65 points hors plage dont **40 latitude/longitude inversées** et **15 points à (0, 0)** ; 243 points à plus de 100 km du centre de leur ville ; 20 coordonnées sans décimales (0 décimale au lieu de 6) ; 81 livraisons antérieures à la commande ; 15 livraisons de commandes inconnues ; 25 commandes ANNULEE livrées.
- **Documents** : 95 PDF non rattachables (40 sans commande et 55 commande inconnue) ; **15 PDF de 0 octet et 0 page** (par exemple `FAC-2026-CORROMPU.pdf`, vide dans l'échantillon) ; 20 empreintes `sha256` partagées par 2 fichiers ; 120 PDF dont la commande de l'index diffère de celle du XML. Ouverture de 3 PDF de l'échantillon : contenu (numéro, commande, client, date, HT, TVA, TTC) = XML, mais la `taille_octets` de l'index (88 999 o) ne correspond pas à la taille réelle de l'échantillon (1,7 Ko) ; pour `FAC-2026-004750`, le PDF et le XML datent la facture du 11/10 alors que la commande CMD1179 est du 20/10.
- **Avis** : 59 avis avec e-mail ou téléphone ; 31 notes hors échelle 1-5 (15 à 0, 8 à 6, 8 à 10) ; 80 textes vides ; 96 textes à l'encodage cassé (`Ã`, `Â`) ; 175 avis en double (même client, produit et texte) ; 47 produits inexistants et 20 clients inconnus. **Représentativité** : seuls 3 042 clients distincts sur 15 352 (19,8 %) ont écrit un avis, et la note 5 pèse 55,6 % des avis (2 278 / 4 100) : les avis ne représentent pas la clientèle.

## 6. Anomalies qualifiées : erreur certaine / suspicion / cas légitime

| # | Anomalie (source) | Preuve | Classement |
|---|---|---|---|
| 1 | Champ `client_id` renommé en `customerId` en schéma 2.0 (JSON) | 2 010 messages v2.0 à `client_id` vide, tous datés du 01/10 au 31/10 | **Erreur certaine** (rupture de contrat) |
| 2 | Commande facturée deux fois (XML, **tabulaire hors**) | CMD25001 (C1042) : FAC-2026-004430 et FAC-2026-004848, même TTC 154,39 | **Erreur certaine** : 310 commandes |
| 3 | **Trou de 6 h sur CF-03 (IoT)** | Écart de 365 min le 14/10 à 07:00 ; l'import du 14/10 est chargé avec 792 lignes (au lieu de 864) et le statut SUCCES | **Erreur certaine** (complétude) |
| 4 | **Doublons dans les logs PSP** | 250 `event_id` apparaissent deux fois avec le même contenu (ex. même montant, même commande) | **Erreur certaine** (doublon exact) |
| 5 | **Données personnelles dans des avis (texte)** | ex. « Écrivez-moi : ines.bernard385@example.com » dans un avis publié | **Erreur certaine** (RGPD) |
| 6 | **Coordonnées GPS inversées ou à 0,0** | LV000161 (Toulouse) : latitude 1,4541 et longitude 43,6316 (inversée) ; 15 points à (0, 0) | **Erreur certaine** (inversions, 0,0) / **suspicion** (243 points à > 100 km, dont des fiches « Nice » avec coordonnées toulousaines) |
| 7 | 133 commandes avec un `client_id` inconnu du CRM (JSON) | ex. C20175, C27911 : absents du CRM (15 100 + 312 fiches) | **Suspicion à valider** (client supprimé ? fiche B- non synchronisée ?) |
| 8 | Statut SUSPENDU (39 clients) | présent dans le CRM, absent de STATUT_CLIENT | **Suspicion** : statut métier réel non référencé |
| 9 | 72 horodatages en double le 25/10 entre 02:00 et 02:55 (IoT) | 3 capteurs × 12 pas × 2 = retour à l'heure d'hiver | **Cas légitime** (l'heure locale 02:00-03:00 existe deux fois ; les 80 autres doublons restent des erreurs) |
| 10 | Commande payée deux fois (CMD10114 : 57,27 + 57,28 = 114,55 = TTC) | somme = TTC de la commande | **Cas légitime** (paiement en deux fois) |

Les anomalies #3, #4, #5, #6 sont **hors tableaux** ; #2 touche une source semi-structurée (XML).

## 7. Impacts métier et réglementaires

- **Finance / fiscalité** : doubles factures (310) → TVA déclarée en double, avoirs à émettre ; 59 factures incohérentes ; 77 lignes à 19,6 %.
- **Sécurité alimentaire** : impossible de prouver 0-4 °C pendant 6 h ; un KPI à 99,53 % masque ce trou.
- **RGPD** : exactitude (art. 5.1.d : adresses, doublons de fiches, 25 mineurs possibles), minimisation et sécurité (art. 5.1.c et 32 : 59 avis), base légale (612 consentements vides).
- **Pilotage** : trois chiffres d'affaires incompatibles ; clients actifs gonflés (voir L6).
- **Confiance** : les écarts viennent surtout de ruptures de contrat et d'absence de contrôles bloquants, plus que de saisies isolées.

## 8. Priorités et recommandations

1. **P1** : contrat d'interface et alias `customerId` (R01) ; dépublication des 59 avis (R04) ; avoirs sur les 310 doubles factures (R09) ; rejet de l'import capteurs si < 864 mesures par jour (R06) ; suspension des 3 indicateurs de CA.
2. **P2** : fusion des 60 collisions et des fiches B- (arbitrage métier) ; dédoublonnage des événements PSP et passage en UTC.
3. **P3** : normalisation des référentiels et correction des taux de TVA ; contrôle GPS dans l'application livreur.
4. **Préventif** : listes fermées, contrats versionnés, moniteurs de volume/schéma (voir L6).

Détail et arbitrages : `03_L3_plan_remediation.csv`.

## 9. Mission 4 · Réconciliation de bout en bout

**Dix commandes suivies** (détail complet : `02_annexe_suivi_10_commandes.csv`) :

| Commande | Cas | Ce que montrent les sources |
|---|---|---|
| CMD209 | Exemple du cours | JSON : PAYEE, 149,90 € TTC ; log : 1 PAYMENT_ACCEPTED 149,90 € ; **aucune facture, livraison ni PDF** (les factures ne couvrent que sept.-oct., la commande date du 05/03) |
| CMD10795 | Annulée mais facturée | ANNULEE ; FAC-2026-005189 émise 103,68 € ; paiement 103,68 € puis REFUND -103,68 € : remboursé, **facture non annulée** |
| CMD10114 | Payée en deux fois | 57,27 + 57,28 = 114,55 € = TTC facture : **normal** |
| CMD10008 | Payée puis remboursée | ANNULEE ; ACCEPTED 47,84 € puis REFUND -47,84 € : **normal** |
| CMD10041 | Refus puis acceptation | REFUSED 89,13 € puis ACCEPTED 89,13 € ; facture et PDF cohérents : **normal** |
| CMD25001 | Facturée deux fois | 2 factures (004430 et 004848) de 154,39 € pour un paiement de 154,38 € ; client C1042 (Nadia Benali) ; écart de 0,01 € |
| CMD12697 | Livraison avant commande | commande du 02/04, livraison LIVREE le 29/03 ; aucune facture |
| CMD25063 | PDF vide | 2 factures dont FAC-2026-001034.pdf = 0 octet |
| CMD11872 | Schéma 2.0 | client sous `customerId` (C4247) ; facture, paiement, livraison, PDF cohérents |
| CMD25214 | Statut hors référentiel | statut « LIVRER » ; facture et paiement cohérents |

**Contrôles inter-sources généralisés** (commandes uniques : 25 312) :
- Commandes **annulées** : 1 718 ; dont **30 facturées**, **1 705 avec paiement accepté** (263 sans remboursement) et **25 livrées** → à arbitrer avec la Finance.
- **Livraison avant la commande** : 81 livraisons.
- Commandes **facturées deux fois** : 310 (R09).
- **Paiement accepté ≠ TTC** : sur 4 700 commandes à un seul paiement accepté et facturé, 133 s'écartent de plus de 0,05 € (par exemple CMD5451 : 43 190 € payés pour 431,90 € facturés, soit un facteur 100).
- **Paiement avant commande** (plus d'une heure) : 1 cas.
- Factures sans aucun paiement : 46.

**Commandes à plusieurs événements de paiement** : 3 252 commandes sur 24 541 ayant un paiement (13,3 %). Ce n'est pas forcément une anomalie : ACCEPTED + REFUND 1 330 (remboursement), ACCEPTED + REFUSED 1 129 (refus puis acceptation), ACCEPTED + ACCEPTED 674 (paiement fractionné, ou doublon à vérifier si la somme dépasse le TTC), ACCEPTED + REFUSED + REFUND 69, ACCEPTED + ACCEPTED + REFUND 43.

## 10. Limites

- Données synthétiques : les causes décrites comme « probables » sont des **hypothèses** à valider avec les équipes.
- Les factures XML ne couvrent que sept.-oct. 2026 : les contrôles facture ↔ commande ne portent que sur ces deux mois.
- Le journal `journaux_traitements.csv` n'est pas rapprochable de la volumétrie du fichier JSON (le journal charge 300 à 900 lignes par jour, le fichier ~90) : nous le traitons comme un indicateur de comportement du pipeline, pas comme une preuve de volume.
- Les PDF de l'échantillon sont de petite taille (1,7 Ko) alors que l'index annonce 28-95 Ko : le contrôle du contenu ne porte que sur 11 fichiers.
- Notre reproduction des chiffres publiés (A, B) est approchée (voir L6) ; les écarts restants (0,3 %) ne sont pas expliqués.
- Plusieurs règles de seuil (km, 20 %, 5 %) sont des choix d'équipe, justifiés mais discutables.

## 11. Conclusion

La confiance n'est pas à retirer partout, mais elle est **à conditionner** : les tables de référence (produits, catalogue) sont globalement saines, alors que les flux à contrat changeant (API commandes, facturation, PSP, IoT) ne sont couverts par aucun contrôle bloquant. Les sources les moins fiables sont la facturation (R09 : 88 %), les commandes (R01 : 91,6 %) et le log PSP (R05 : 97,2 %). Les trois actions les plus rentables sont un contrat d'interface, un contrôle bloquant sur la double facturation, et une fiche indicateur unique pour le chiffre d'affaires.
