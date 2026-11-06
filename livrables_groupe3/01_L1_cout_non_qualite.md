# L1 · Coût de non-qualité et lecture de la matrice · Groupe 3

*Complète `01_L1_matrice_donnees_critiques.csv` (13 données critiques issues de 10 sources ; 9 lignes hors tableaux : logs, IoT, JSON, XML, GPS, PDF, texte).*

## 1. Descriptions des sources (une ligne chacune)
| Source | Rôle et structure |
|---|---|
| clients_crm.csv | Fiches clients, tableau de 15 colonnes |
| clients_facturation.csv | Clients de l'ERP, tableau, lien `client_crm_id` vers le CRM |
| produits.csv | Référentiel de 365 produits (TVA, catégorie, froid) |
| commandes_api.json | Documents JSON imbriqués (commande + lignes), 2 versions de schéma |
| factures.xml | XML : facture, lignes avec taux de TVA, totaux HT/TVA/TTC |
| paiements.log | Une ligne de log par événement du prestataire (clé=valeur) + lignes WARN techniques |
| capteurs_froid.csv | Série temporelle, 1 mesure / 5 min par capteur |
| livraisons_gps.csv | Livraison avec adresse et latitude/longitude |
| factures_pdf_index.csv + PDF | Index de fichiers (taille, pages, sha256) + documents |
| avis_clients.csv | Texte libre publié, avec note de 1 à 5 |

## 2. Les trois données les plus critiques (criticité = impact × exposition)
1. **Montant de paiement : 4 × 3 = 12 (critique).** Une erreur fausse la trésorerie, le CA Finance et les remboursements ; la Direction financière, la Direction commerciale et la BI l'utilisent. Constat : 250 `event_id` en double et 60 montants vides.
2. **Statut et identifiant de commande : 4 × 3 = 12 (critique).** Le statut commande le cycle facturation → livraison ; un statut faux conduit à livrer des commandes annulées (25 observées) ou à compter du CA fictif. Utilisé par toute l'entreprise.
3. **Température des chambres froides : 4 × 2 = 8 (critique).** Risque légal et sanitaire (impact 4) ; exposition limitée à la qualité et à la maintenance, mais conséquences pour toute l'entreprise en cas de rappel. Constat : trou de 6 h chargé en SUCCES.

Justification de notre notation : nous avons noté « 4 » les risques légaux ou d'arrêt d'activité (RGPD, sécurité alimentaire, fiscalité), « 3 » les pertes d'argent ou de client, conformément à la grille du dossier ; une autre équipe pourrait noter l'exposition différemment.

## 3. Coût de non-qualité (ordre de grandeur, **hypothèses explicites**)
| Poste | Volume observé | Hypothèses | Coût |
|---|---|---|---|
| Double facturation | 310 commandes sur 2 mois, soit 155 / mois | 1 réclamation = 25 min service client + 15 min comptabilité (avoir) = 0,67 h; coût chargé 38 €/h | 155 × 0,67 × 38 ≈ **3,9 k€/mois**, **≈ 47 k€/an** |
| Colis envoyés à une ancienne adresse (incident de mars) | 47 colis par épisode | réexpédition 12 € + 30 min de SAV à 38 €/h | 47 × (12 + 19) ≈ **1,5 k€ par épisode** |
| Deux chiffres d'affaires | 1 rapprochement par mois | 2 analystes × 4 h × 55 €/h | 440 €/mois ≈ **5,3 k€/an** |
| Reprise des fiches clients en doublon | 60 collisions + 312 fiches B- | 372 fiches × 10 min × 38 €/h | ≈ **2,4 k€ une fois** |
| Rupture du froid non prouvée | 1 chambre, 6 h | perte potentielle de 1 lot : 3 000 € × probabilité 10 % | ≈ **300 €** par épisode (sans compter le risque réglementaire, non chiffré) |
| **Total annuel indicatif** | | | **≈ 55 à 60 k€/an** |

*Ces montants sont des hypothèses pédagogiques à remplacer par les coûts réels de NovaCommerce ; ils n'incluent ni l'amende éventuelle (RGPD, fiscale) ni la perte de confiance.*

## 4. Qualité, conformité et confiance (RGPD art. 5.1.d)
Le RGPD impose que les données personnelles soient **exactes et tenues à jour** : les 60 identifiants partagés entre deux personnes, les 579 adresses divergentes entre CRM et ERP et les 47 colis mal adressés sont des manquements potentiels à ce principe. Mais la qualité va au-delà de la conformité : une direction qui reçoit deux chiffres d'affaires ou un taux de froid de 99,53 % sans trou visible ne peut pas décider sereinement. Mesurer et tracer la qualité est donc la condition de la confiance dans les décisions, et de la capacité à la prouver en cas de contrôle (CNIL, fiscal, sanitaire).
