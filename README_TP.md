# NovaCommerce · jeu de données du TP DATE732

NovaCommerce est une **entreprise fictive** : épicerie fine et maison en ligne, 12 boutiques, 2 entrepôts dont un frais.
Toutes les données sont **synthétiques** (noms, e-mails en example.com/.net/.org, IBAN, coordonnées : rien n'est réel).

## À lire en premier
`00_Dossier_NovaCommerce.pdf` (2 pages) : l'entreprise, l'incident de mars 2026, les acteurs et les neuf familles de sources. C'est le support de la mise en pratique 1 (matrice des données critiques).

## Contenu du dossier `donnees/`

| Fichier | Type | Contenu | Volume |
|---|---|---|---|
| `clients_crm.csv` | Tabulaire | Fiches clients du CRM | 15412 lignes |
| `clients_facturation.csv` | Tabulaire | Clients de l'ERP de facturation | 11805 lignes |
| `produits.csv` | Tabulaire | Référentiel produits | 365 lignes |
| `referentiels.csv` | Tabulaire | Listes de valeurs autorisées | — |
| `commandes_api.json` | Semi-structuré (JSON) | Commandes reçues par l'API du site et des caisses | 25422 commandes |
| `factures.xml` | Semi-structuré (XML) | Factures de septembre et octobre 2026 | 5214 factures |
| `paiements.log` | Logs | Événements du prestataire de paiement | 28155 événements |
| `avis_clients.csv` | Texte libre | Avis publiés sur le site | 4100 avis |
| `capteurs_froid.csv` | Série temporelle (IoT) | Températures des chambres froides, octobre 2026, toutes les 5 min | 26788 mesures |
| `livraisons_gps.csv` | Géographique | Livraisons et coordonnées GPS | 14982 livraisons |
| `factures_pdf_index.csv` + `factures_pdf_echantillon/` | Documents | Index des PDF déposés et un échantillon | — |
| `kpi_bruts_a_verifier.csv` | Indicateurs | Chiffres publiés par les tableaux de bord, **non certifiés** | 5 indicateurs |
| `flux_lineage.csv` | Métadonnées | Flux déclarés par l'IT, **à vérifier** | 7 flux |
| `journaux_traitements.csv` | Journalisation | Exécutions des chargements d'octobre | — |

Le dossier `modeles/` contient les trames des six livrables (L1 à L6) et le catalogue de métadonnées à compléter.

## Démarrer
1. **Si pandas ne vous est pas familier** : faites d'abord `00_bases_python_pandas.ipynb` (≈ 45 min, exercices sur NovaCommerce).
2. Ouvrez `audit_novacommerce.ipynb` (Jupyter, VS Code ou Google Colab : déposez aussi le dossier `donnees/`).
   Il charge les quatorze sources, fournit une boîte à outils (doublons, référentiels, formats, jointures, capteurs figés, GPS, volumes)
   et suit les neuf missions du document `TP_DATE732_NovaCommerce_etudiants.docx`.
3. Les parties 1 à 5 s'exécutent telles quelles (règles R01 à R08). Les cellules **À vous** sont à compléter.

Sans Python : les fichiers CSV s'ouvrent dans Excel ou LibreOffice (importer en **texte** pour ne pas perdre les zéros initiaux) ;
le JSON et le XML s'ouvrent avec Power Query (Données › Obtenir des données › À partir d'un fichier).

## Consignes
- Ne modifiez jamais les fichiers bruts : travaillez sur des copies.
- Distinguez **erreur certaine**, **suspicion à valider** et **cas légitime** : certaines valeurs rares sont correctes.
- Le jeu contient des anomalies **que les règles R01 à R08 ne détectent pas**. Les trouver fait partie du travail.
- Une anomalie corrigée n'est jamais « devinée » : on la signale, on la trace, on la fait valider.
