# L4 · Traçabilité, lineage et journaux · Groupe 3

*Complète `04_L4_referentiel_regles.csv` (12 règles dont au moins 7 hors tableaux), `04_L4_catalogue_metadonnees.csv` (47 champs) et `04_L4_registre_donnees_critiques.csv` (6 données).*

## 1. Journaux de traitement (`journaux_traitements.csv`, 94 exécutions)

| Traitement | Exécutions | SUCCES | ECHEC_SEUIL | Taux de rejet |
|---|---|---|---|---|
| import_capteurs | 31 | 31 | 0 | 0,09 % |
| import_paiements | 31 | 31 | 0 | 0,18 % |
| import_commandes_api | 32 | 14 | 18 | 5,24 % |

**Observation 1 · bilan et séries d'échecs.** `lignes_entree = lignes_chargees + lignes_rejetees` est vérifié pour les 94 exécutions. Les échecs de l'import des commandes forment **une série continue : première date le 15/10/2026 à 01:10 UTC**, 17 échecs quotidiens consécutifs puis un 18e le 31/10 (run de 10 000 lignes à 08:15, volume anormal : environ 15 fois la moyenne quotidienne). Les rejets passent de 0-3 à 60-107 par jour, tous sur la règle R01.

**Observation 2 · ce que SUCCES ne garantit pas.** Le 14/10, l'import des capteurs est en **SUCCES avec 792 lignes au lieu de 864** (3 capteurs × 288), soit -8,3 % : le statut valide le bilan entrée = chargé + rejeté, pas la complétude. Les 72 mesures manquantes sont le trou de 6 h de CF-03. Un SUCCES garantit seulement que le bilan est cohérent et que le traitement s'est terminé ; il ne garantit ni la complétude, ni l'exactitude, ni la fraîcheur. Le volume d'entrée est lui-même celui reçu, pas celui attendu.

**Écart non expliqué (à valider avec l'IT).** Le schéma 2.0 apparaît dès le 01/10 dans le JSON (73 % des commandes d'octobre), mais les échecs du pipeline ne commencent que le 15/10 : hypothèse, le pipeline tolérait l'alias avant cette date, ou la règle R01 du journal n'a été durcie que le 15/10. La volumétrie du journal (300 à 900 commandes/jour) n'est pas non plus rapprochable du fichier JSON (~90/jour).

## 2. Lineage du chiffre d'affaires (flux L01 → L04 → L07, plus L03)

```
Site web / caisses ──L01──► Zone brute commandes_brutes ─┐
 (copie telle que reçue,          règle : aucune         │
  aucun contrôle)                                        ├─L04─► Entrepôt fait_ventes ──L07──► Tableau A
PSP paiements.log ──L03──► Zone brute paiements_bruts ───┘   (jointure commandes × paiements,        (CA = somme TTC)
 (parsing + dédoublonnage, R05)                              somme des montants, règle R01)          règle : aucune
```

| Flux | Déclaré | Observé au Bloc 1 | Verdict |
|---|---|---|---|
| L01 | « Copie telle que reçue », règles : aucun | 2 143 commandes sans client exploitable (schéma 2.0), 110 identifiants dupliqués | **Incomplet** : aucun contrôle d'entrée alors que le contrat a changé |
| L03 | « Parsing des logs et dédoublonnage », R05 | 250 `event_id` en double, 303 horodatages hors UTC encore présents, 60 montants vides, 122 événements de commandes inconnues | **Faux** : le dédoublonnage n'est pas effectif sur l'extraction étudiée |
| L04 | « Jointure commandes × paiements, somme des montants » | Relation 1:N : 2 739 commandes d'octobre → 2 961 lignes après jointure (+8,1 %), 315 commandes à plusieurs événements | **Faux / dangereux** : multiplie les montants (voir L6) |
| L07 | « Somme TTC », règles : aucun | Somme du TTC brut, doublons de commandes et aberrations incluses (48 216 € pour une commande de 419 € HT) | **Incomplet** |

**Contrôles qui devraient être traversés** : alias de schéma et unicité de `commande_id` (L01), unicité de `event_id` et UTC (L03), contrôle de cardinalité avant jointure (L04), réconciliation du total avec les paiements nets et fiche indicateur (L07).

## 3. Lineage du flux IoT (L06)

```
Capteurs CF-01..03 ─► Plateforme IoT ──L06──► Entrepôt mesures_froid ──► KPI « conformité chaîne du froid »
 (1 mesure / 5 min)     (unité C ou F)   agrégation horaire (moyenne)      (part des lignes entre 0 et 4)
                                         règle : R06
```

| Déclaré | Observé | Verdict |
|---|---|---|
| Agrégation horaire (moyenne), règle R06 | Une **moyenne horaire masque** les excursions de quelques minutes et un trou ; un trou de 72 mesures ne se voit pas dans une moyenne ; R06 ne détecte ni les °F (50), ni les valeurs vides (20), ni les valeurs figées (65) | **Incomplet** |

Contrôles à ajouter : volume par jour (864), unité, vide, valeur figée, **avant** toute agrégation.

## 4. Traçabilité et souveraineté (mission 6, point 34)

Pour chaque donnée critique, le registre (`04_L4_registre_donnees_critiques.csv`) documente : lieu d'hébergement, droit applicable, réversibilité et durée de conservation. Les valeurs sont des **hypothèses de travail à confirmer** par l'IT et le DPO (aucune information réelle n'existe dans les sources).

Pour les **accès et transferts hors UE**, nous recommandons de tenir : (1) un registre des sous-traitants (PSP, hébergeur, éditeur IoT, application livreurs) avec la localisation des serveurs et les accès à distance depuis un pays tiers ; (2) pour chaque transfert, l'outil juridique retenu (décision d'adéquation, dont le Data Privacy Framework, ou clauses contractuelles types) et l'analyse d'impact du transfert ; (3) un journal des accès conforme à la recommandation de la CNIL sur la journalisation ; (4) une clause de réversibilité (format, délai, effacement certifié).

**Point de vigilance** : au 1er novembre 2026, la CJUE n'a pas encore statué sur le pourvoi C-703/25 P contre le Data Privacy Framework (information fournie par l'énoncé du TP). Le DPF reste donc valable à cette date, mais il faut prévoir un plan de repli (clauses contractuelles types, hébergement UE) pour les transferts vers les États-Unis.
