"""Analyse NovaCommerce · Groupe 3 · exécute les règles R01 à R10 et enregistre synthese_regles.csv.
Usage : python3 analyse_groupe3.py   (lit /home/user/nova/donnees, n'écrit que dans livrables_groupe3/)"""
from nv import *
OUT = Path(__file__).resolve().parent.parent
S = []
def regle(rid, desc, ctrl, n, unite):
    S.append({'règle': rid, 'description': desc, 'unité comptée': unite, 'contrôlés': ctrl, 'en anomalie': int(n),
              '% conformes': round(100 * (ctrl - n) / ctrl, 2)})

ids_crm = set(clients.client_id)
# R01
regle('R01', 'commande -> client_id existant dans le CRM', len(commandes), (~commandes.client_id.isin(ids_crm)).sum(), 'commandes (lignes JSON)')
# R02
regle('R02', 'client_id unique dans le CRM', len(clients), clients.client_id.duplicated(keep=False).sum(), 'lignes CRM (60 clés distinctes)')
# R03
f = factures.copy()
for c in ['total_ht', 'total_tva', 'total_ttc']: f[c] = pd.to_numeric(f[c], errors='coerce')
regle('R03', 'TTC = HT + TVA (0,01 €)', len(f), ((f.total_ttc - f.total_ht - f.total_tva).abs() > 0.01).sum(), 'factures')
# R04
pat = r'FR\d{2}(?:\s?\d{4}){5}\s?\d{3}|\b0[1-9](?:[\s.]?\d{2}){4}\b|[\w.+-]+@[\w-]+\.[\w.]+'
regle('R04', 'aucune donnée personnelle dans un avis publié', len(avis), avis.texte.str.contains(pat, regex=True).sum(), 'avis')
# R05
p = paiements
regle('R05', 'event_id unique et horodatage UTC (Z)', len(p), (p.event_id.duplicated(keep=False) | ~p.event_time.str.endswith('Z')).sum(), 'événements PSP')
# R06
c = capteurs.copy(); c['t'] = pd.to_numeric(c.temperature, errors='coerce'); c['h'] = pd.to_datetime(c.horodatage_local)
hp = ((c.t < -40) | (c.t > 60)).sum(); c = c.sort_values(['capteur_id', 'h']); c['e'] = c.groupby('capteur_id').h.diff().dt.total_seconds() / 60
regle('R06', 'plage -40/+60 °C et pas de trou > 5 min', len(c), hp + (c.e > 5).sum(), 'mesures (dont 1 trou de 365 min)')
# R07
g = livraisons.copy(); g['lat'] = pd.to_numeric(g.latitude); g['lon'] = pd.to_numeric(g.longitude)
regle('R07', 'coordonnées en France métropolitaine', len(g), (~g.lat.between(41, 51.5) | ~g.lon.between(-5.5, 10)).sum(), 'livraisons')
# R08
regle('R08', 'PDF rattaché à une commande existante', len(pdf), (~pdf.commande_id.isin(set(commandes.commande_id))).sum(), 'PDF')
# R09 : une commande n'est facturée qu'une fois
fv = f[f.commande_id.notna()]
regle('R09', "une commande n'est facturée qu'une seule fois (1 numéro par commande)", len(fv), fv.commande_id.duplicated(keep=False).sum(), 'factures (310 commandes concernées)')
# R10 : capteur : unité °C, valeur renseignée, pas de valeur figée sur 1 h
fig = valeur_figee(capteurs, 'capteur_id', 'horodatage_local', 'temperature')
mauv = capteurs[(capteurs.unite != 'C') | (capteurs.temperature == '')]
bad = set(zip(fig.capteur_id, fig.horodatage_local)) | set(zip(mauv.capteur_id, mauv.horodatage_local))
regle('R10', 'capteur : unité °C, valeur présente, pas de valeur figée sur 1 h', len(capteurs), len(bad), 'mesures (50 °F, 20 vides, 65 figées)')
t = pd.DataFrame(S); t.to_csv(OUT / 'synthese_regles.csv', index=False); print(t.to_string())
