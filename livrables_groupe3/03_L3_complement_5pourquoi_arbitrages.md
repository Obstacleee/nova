# L3 · 5 pourquoi, priorisation et arbitrages · Groupe 3

*Complète `03_L3_plan_remediation.csv` (9 anomalies : 1 d'intégrité, 1 de référentiel, 2 qui touchent un indicateur, 5 hors tableaux ou semi-structurées).*

## 1. Cinq pourquoi · anomalie R01 (commandes sans client exploitable)
Les **faits** sont notés (F), les **hypothèses** (H).
1. *Pourquoi 2 143 commandes (8,4 %) échouent-elles à R01 ?* → Parce que 2 010 messages (schéma 2.0) n'ont plus de `client_id` : l'identifiant est dans `customerId` (F).
2. *Pourquoi le champ a-t-il changé ?* → Parce que le site web a livré une version 2.0 du message le 01/10/2026 qui renomme `client_id` en `customerId`, `montant_total_ttc` en `total_ttc` et ne renseigne plus `contact.telephone` (F).
3. *Pourquoi personne n'a-t-il été prévenu ?* → Parce qu'il n'existe ni contrat d'interface ni délai de prévenance : le flux L01 est une « copie telle que reçue » sans aucune règle (F, `flux_lineage.csv`).
4. *Pourquoi le défaut n'a-t-il pas été détecté plus tôt ?* → Parce que les imports sont restés en SUCCES jusqu'au 14/10 et que le premier ECHEC_SEUIL date du 15/10, soit 14 jours après le premier message 2.0 (F) ; le pipeline tolérait probablement l'alias avant cette date (H).
5. *Pourquoi aucun responsable n'a-t-il réagi ?* → Parce qu'aucun Data Owner n'est nommé pour l'interface commandes et que la gestion du changement n'inclut pas la Data (H, à valider).

**Cause racine retenue** : absence de gouvernance de l'interface (pas de contrat ni de propriétaire). L'action curative (alias) traite le symptôme ; l'action préventive (contrat versionné) traite la cause.

## 2. Priorités (impact × urgence × effort)
| Priorité | Anomalies | Argument |
|---|---|---|
| P1 | R01/contrat API, double facturation (R09), trou de froid, avis RGPD (R04), conflit de CA | Impact légal, financier ou sanitaire immédiat; effort faible à moyen (alias, avoirs, filtre) |
| P2 | Doublons clients (R02), logs PSP (R05), PDF (R08) | Impact réel mais pas d'exposition immédiate; effort moyen |
| P3 | Référentiels, GPS (R07) | Impact limité, correction progressive |

Correction **à la source** pour R09, R02, R04, R07, R08 (sinon le défaut se reproduit); **dans l'ETL** pour les alias de schéma (transitoire), les statuts normalisés, le dédoublonnage `event_id` et le contrôle de volume, car on ne peut pas modifier le système amont immédiatement.

## 3. Types d'actions
- **Curatives** : alias `customerId`, avoirs, dépublication, récupération des mesures, régénération des PDF.
- **Préventives** : contrat d'interface, clé unique `commande_id` côté ERP, filtre R04 bloquant, rejet si volume capteurs < 864/jour, listes fermées.
- **Contrôles de validation** : taux R01 >= 99 % sur 7 jours, 0 commande multi-facturée, 0 avis avec donnée personnelle sur balayage hebdomadaire.

## 4. Corrections qui demandent un arbitrage métier avant exécution
1. **Fusion de clients (R02)** : choisir la fiche survivante entre C1042 (WEB, mise à jour le 30/10/2026) et B-77810 (CAISSE) pour Nadia Benali ; un même e-mail ne prouve pas l'identité (homonymes) → Data Owner client.
2. **Double facturation (R09)** : quelle des deux factures annuler (avoir) et que faire du paiement ; décision Finance (impact TVA).
3. **Commandes annulées mais facturées, payées sans remboursement ou livrées** (30, 263 et 25 cas) : rembourser, réactiver ou facturer.
4. **Statut SUSPENDU et taux de TVA des 3 produits à 19,6 %** : ajouter au référentiel ou corriger ; décision Finance et Marketing.
