from nv import *
import csv
cu=commandes.drop_duplicates('commande_id').set_index('commande_id')
f=factures; p=paiements.drop_duplicates('event_id'); g=livraisons; pi=pdf
fac_n=f.groupby('commande_id').size(); 
typ=p.groupby('commande_id').type.apply(lambda s:' + '.join(sorted(s)))
pick={}
def first(cond,label):
    for cid in cond:
        if cid not in pick.values(): pick[label]=cid; return
pick['Exemple du cours (payée, hors périmètre factures/livraisons)']='CMD209'
ann=set(cu[cu.statut=='ANNULEE'].index)
first([c for c in fac_n.index if c in ann and c in set(g.commande_id)] or [c for c in fac_n.index if c in ann],'Annulée mais facturée (et livrée si possible)')
first([c for c in typ[typ=='PAYMENT_ACCEPTED + PAYMENT_ACCEPTED'].index if c in set(f.commande_id)],'Payée deux fois (2 PAYMENT_ACCEPTED)')
first([c for c in typ[typ=='PAYMENT_ACCEPTED + REFUND'].index if c in cu.index],'Payée puis remboursée')
first([c for c in typ[typ=='PAYMENT_ACCEPTED + PAYMENT_REFUSED'].index if c in set(f.commande_id)],'Refus puis acceptation')
first([c for c in fac_n[fac_n>1].index if c in cu.index],'Facturée deux fois')
gg=g.copy(); gg['d']=en_date(gg.date_livraison); gg['dc']=gg.commande_id.map(en_date(cu.date_commande))
first(gg[gg.d<gg.dc].commande_id.tolist(),'Livraison avant la commande')
pv=pi[pi.taille_octets=='0']; first(pv.commande_id[pv.commande_id.isin(cu.index)].tolist(),'PDF vide (0 octet)')
first(cu[(cu.schema_version=='2.0')].index[cu[(cu.schema_version=='2.0')].index.isin(f.commande_id)].tolist(),'Schema 2.0 (client sous customerId)')
first(cu[cu.statut=='LIVRER'].index[cu[cu.statut=='LIVRER'].index.isin(f.commande_id)].tolist(),'Statut hors référentiel (LIVRER)')
rows=[]
for lab,c in pick.items():
    r=cu.loc[c]; fa=f[f.commande_id==c]; pa=p[p.commande_id==c]; li=g[g.commande_id==c]; pd_=pi[pi.commande_id==c]
    cid=r.get('client_id') if isinstance(r.get('client_id'),str) else r.get('customerId')
    rows.append({'cas':lab,'commande_id':c,'date_commande':r.date_commande,'schema':r.schema_version,'statut':r.statut,'client':cid,
      'ttc_commande':r.montant_total_ttc if isinstance(r.montant_total_ttc,(str,float)) and r.montant_total_ttc==r.montant_total_ttc else r.total_ttc,
      'factures':' ; '.join(f'{a.numero or "(sans numéro)"} {a.date_emission} TTC {a.total_ttc}' for a in fa.itertuples()) or 'aucune',
      'paiements':' ; '.join(f'{a.type} {a.montant or "vide"}' for a in pa.itertuples()) or 'aucun',
      'livraison':' ; '.join(f'{a.statut_livraison} {a.date_livraison[:16]}' for a in li.itertuples()) or 'aucune',
      'pdf':' ; '.join(f'{a.fichier} {a.taille_octets} o' for a in pd_.itertuples()) or 'aucun'})
out=pd.DataFrame(rows); out.to_csv('/home/user/nova/livrables_groupe3/02_annexe_suivi_10_commandes.csv',index=False,encoding='utf-8-sig')
pd.set_option('display.width',300); pd.set_option('display.max_colwidth',70); print(out.to_string())
