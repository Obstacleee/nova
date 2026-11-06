import warnings; warnings.filterwarnings('ignore')
display=lambda *a,**k: None
import json, re
import xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
import pandas as pd

pd.set_option('display.max_columns', 30)
pd.set_option('display.width', 160)
D = Path('/home/user/nova/donnees')   # dossier des données brutes, à côté du notebook

lire = lambda nom: pd.read_csv(D / nom, dtype=str, keep_default_na=False)
clients, erp, produits = lire('clients_crm.csv'), lire('clients_facturation.csv'), lire('produits.csv')
refs = pd.read_csv(D / 'referentiels.csv', dtype=str)
print('clients CRM :', len(clients), '· clients ERP :', len(erp), '· produits :', len(produits), '· codes de référence :', len(refs))

# JSON : une ligne par commande, et une ligne par article commandé
with open(D / 'commandes_api.json', encoding='utf-8') as f:
    brut = json.load(f)
commandes = pd.json_normalize(brut)
lignes = pd.json_normalize(brut, record_path='lignes', meta=['commande_id'])
print('commandes :', len(commandes), '· lignes de commande :', len(lignes))
print('colonnes :', list(commandes.columns))

# XML : une ligne par facture
racine = ET.parse(D / 'factures.xml').getroot()
factures = pd.DataFrame([{
    'numero': f.get('numero'), 'commande_id': f.findtext('commande_id'), 'client_id': f.findtext('client_id'),
    'date_emission': f.findtext('date_emission'), 'total_ht': f.findtext('total_ht'), 'total_tva': f.findtext('total_tva'),
    'total_ttc': f.findtext('total_ttc'), 'devise': f.findtext('devise'), 'nb_lignes': len(f.find('lignes')),
} for f in racine.findall('facture')])
print('factures :', len(factures))

# Logs : un événement de paiement par ligne. On compte aussi les lignes qui ne correspondent pas au motif.
motif = re.compile(r'^(?P<recu>\S+) (?P<niveau>\w+) psp-gateway event_id=(?P<event_id>\S+) '
                   r'event_time=(?P<event_time>.+?) type=(?P<type>\S+) commande_id=(?P<commande_id>\S+) '
                   r'montant=(?P<montant>\S*) devise=(?P<devise>\S+) moyen=(?P<moyen>\S+)$')
evts, autres = [], []
with open(D / 'paiements.log', encoding='utf-8') as f:
    for ligne in f:
        m = motif.match(ligne.strip())
        (evts.append(m.groupdict()) if m else autres.append(ligne.strip()))
paiements = pd.DataFrame(evts)
print('événements de paiement :', len(paiements), '· autres lignes :', len(autres), '→ exemple :', autres[:1])

# Texte libre, série temporelle IoT, géographique, documents, et les fichiers de la Partie II
avis, capteurs, livraisons, pdf = lire('avis_clients.csv'), lire('capteurs_froid.csv'), lire('livraisons_gps.csv'), lire('factures_pdf_index.csv')
journaux, lineage, kpi = lire('journaux_traitements.csv'), lire('flux_lineage.csv'), lire('kpi_bruts_a_verifier.csv')
print('avis :', len(avis), '· mesures :', len(capteurs), '· livraisons :', len(livraisons), '· PDF indexés :', len(pdf))
print('exécutions journalisées :', len(journaux), '· flux déclarés :', len(lineage), '· KPI publiés :', len(kpi))

def profil(df, top=4):
    """Une ligne par colonne : vides, % vides, valeurs distinctes, valeurs les plus fréquentes."""
    res = []
    for col in df.columns:
        s = df[col].astype(str)
        vides = s.str.strip().isin(['', 'nan', 'None', '<NA>']).sum()
        res.append({'colonne': col, 'vides': vides, '% vides': round(100 * vides / len(df), 2),
                    'distinctes': s.nunique(), 'plus fréquentes': s.value_counts().head(top).to_dict()})
    return pd.DataFrame(res)


synthese = []

def resultat(regle, description, controles, anomalies, exemples=None):
    """Enregistre une règle dans la synthèse et affiche quelques exemples."""
    n = anomalies if isinstance(anomalies, (int, np.integer)) else len(anomalies)
    taux = round(100 * (controles - n) / controles, 2) if controles else None
    synthese.append({'règle': regle, 'description': description, 'contrôlés': controles, 'en anomalie': n, '% conformes': taux})
    print(f'{regle} · {description}\n  contrôlés : {controles} · en anomalie : {n} · conformes : {taux} %')
    if exemples is not None and len(exemples):
        display(exemples.head(5))


def hors_referentiel(serie, type_ref, normaliser=False):
    """Valeurs absentes de referentiels.csv pour ce type (normaliser=True : ignore casse et espaces)."""
    codes = set(refs.loc[refs['type_referentiel'] == type_ref, 'code'])
    s = serie.fillna('').astype(str)
    if normaliser:
        s = s.str.strip().str.upper()
    hors = serie[~s.isin(codes)]
    print(f'{type_ref} : {len(hors)} valeurs hors référentiel sur {len(serie)} → {hors.value_counts(dropna=False).head(6).to_dict()}')
    return hors


def doublons(df, cles):
    """Toutes les lignes dont la clé est dupliquée. Affiche lignes ET clés distinctes."""
    cles = [cles] if isinstance(cles, str) else cles
    m = df.duplicated(subset=cles, keep=False)
    print(f'{cles} : {m.sum()} lignes concernées · {df.loc[m, cles].drop_duplicates().shape[0]} clés distinctes concernées')
    return df[m].sort_values(cles)


def format_invalide(serie, motif, vides_acceptes=False):
    """Valeurs qui ne respectent pas le motif (expression régulière ancrée au début)."""
    s = serie.fillna('').astype(str)
    ko = ~s.str.match(motif)
    if vides_acceptes:
        ko &= s.str.strip() != ''
    print(f'{ko.sum()} valeurs hors format sur {len(s)}')
    return serie[ko]


def en_nombre(serie):
    """Conversion en nombre ; affiche le nombre de valeurs non vides non convertibles."""
    n = pd.to_numeric(serie, errors='coerce')
    echecs = n.isna() & serie.notna() & (serie.astype(str).str.strip() != '')
    if echecs.any():
        print(f'{echecs.sum()} valeurs non numériques, par exemple {serie[echecs].astype(str).unique()[:4].tolist()}')
    return n


def en_date(serie, utc=True):
    """Conversion ISO 8601 (avec ou sans fuseau) ; affiche les échecs. Sans fuseau, la valeur est SUPPOSÉE en UTC."""
    d = pd.to_datetime(serie, format='ISO8601', errors='coerce', utc=utc)
    echecs = d.isna() & serie.notna() & (serie.astype(str).str.strip() != '')
    if echecs.any():
        print(f'{echecs.sum()} dates non ISO 8601, par exemple {serie[echecs].astype(str).unique()[:4].tolist()}')
    return d


def orphelins(df, col, cible, col_cible):
    """Références vides et références absentes de la table cible."""
    s = df[col]
    vide = s.isna() | (s.astype(str).str.strip() == '')
    inconnu = ~vide & ~s.isin(set(cible[col_cible]))
    print(f'{col} → {col_cible} : {vide.sum()} vides · {inconnu.sum()} inconnues · sur {len(df)}')
    return df[vide | inconnu]


def controle_jointure(gauche, droite, cle_g, cle_d=None):
    """Cardinalité d'une jointure et effet sur le nombre de lignes, AVANT de l'utiliser."""
    cle_d = cle_d or cle_g
    mg, md = gauche[cle_g].value_counts().max(), droite[cle_d].value_counts().max()
    card = f"{'1' if mg == 1 else 'N'}:{'1' if md == 1 else 'N'}"
    j = gauche.merge(droite, left_on=cle_g, right_on=cle_d, how='inner')
    print(f'cardinalité {card} (max {mg} à gauche, {md} à droite) · {len(gauche)} lignes à gauche → {len(j)} après jointure')
    return card


def valeur_figee(df, groupe, temps, valeur, fenetre='1h', min_points=12):
    """Lignes où la valeur est strictement constante sur toute la fenêtre glissante (écart-type nul)."""
    out = []
    for g, d in df.assign(_t=pd.to_datetime(df[temps]), _v=pd.to_numeric(df[valeur], errors='coerce')).sort_values('_t').groupby(groupe):
        r = d.set_index('_t')['_v'].rolling(fenetre)
        fig = (r.std() == 0) & (r.count() >= min_points)
        out.append(d[fig.values])
    res = pd.concat(out).drop(columns=['_t', '_v'])
    print(f'{len(res)} mesures dans une fenêtre de {fenetre} sans aucune variation')
    return res


def distance_km(lat1, lon1, lat2, lon2):
    """Distance à vol d'oiseau (formule de haversine), en km."""
    lat1, lon1, lat2, lon2 = (np.radians(pd.to_numeric(x, errors='coerce')) for x in (lat1, lon1, lat2, lon2))
    a = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    return 6371 * 2 * np.arcsin(np.sqrt(a))


def distance_au_centre(df, ville='ville', lat='latitude', lon='longitude'):
    """Distance de chaque point au centre observé de sa ville (médiane des points de la ville)."""
    d = df.assign(_lat=pd.to_numeric(df[lat], errors='coerce'), _lon=pd.to_numeric(df[lon], errors='coerce'))
    centre = d.groupby(ville)[['_lat', '_lon']].transform('median')
    return distance_km(d['_lat'], d['_lon'], centre['_lat'], centre['_lon'])


def ecart_a_la_reference(par_jour, fenetre=7):
    """Écart (%) de chaque jour à la moyenne des `fenetre` jours précédents."""
    ref = par_jour.rolling(fenetre).mean().shift(1)
    return pd.DataFrame({'valeur': par_jour, 'reference': ref.round(1), 'ecart_%': (100 * (par_jour - ref) / ref).round(1)})


def suivre(commande_id):
    """Affiche une commande dans toutes les sources."""
    vues = {'commande (JSON)': commandes[commandes['commande_id'] == commande_id].drop(columns=['lignes']),
            'factures (XML)': factures[factures['commande_id'] == commande_id],
            'paiements (logs)': paiements[paiements['commande_id'] == commande_id],
            'livraisons (GPS)': livraisons[livraisons['commande_id'] == commande_id],
            'PDF indexés': pdf[pdf['commande_id'] == commande_id]}
    for nom, v in vues.items():
        print(f'— {nom} : {len(v)} ligne(s)')
        if len(v):
            display(v)

print('boîte à outils prête')


def jour(s): return en_date(s).dt.strftime('%Y-%m-%d')
