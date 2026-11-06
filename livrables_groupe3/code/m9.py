from nv import *
cm=commandes.copy()
cu=cm.drop_duplicates('commande_id').copy()
cu['d']=en_date(cu.date_commande)
# octobre en heure locale (Europe/Paris)
cu['dl']=cu.d.dt.tz_convert('Europe/Paris'); oc=cu[(cu.dl>='2026-10-01')&(cu.dl<'2026-11-01')]
print('commandes octobre uniques',len(oc), 'brutes (avec doublons)', ((en_date(cm.date_commande).dt.tz_convert('Europe/Paris')>='2026-10-01')&(en_date(cm.date_commande).dt.tz_convert('Europe/Paris')<'2026-11-01')).sum())
ttc_raw=pd.to_numeric(cm.assign(t=cm.montant_total_ttc.fillna(cm.total_ttc)).t,errors='coerce')
cm['dl']=en_date(cm.date_commande).dt.tz_convert('Europe/Paris'); cm['ttc']=ttc_raw
cmo=cm[(cm.dl>='2026-10-01')&(cm.dl<'2026-11-01')]
print('A reproduit : somme ttc brut octobre (avec doublons)',round(cmo.ttc.sum(),2),'| publié 568367.00')
cmo2=cm[(cm.date_commande>='2026-10-01')&(cm.date_commande<'2026-11-01')]; print('A (filtre texte sur date_commande)',round(cmo2.ttc.sum(),2))
# lignes recalculées
l=lignes.copy(); l['m']=en_nombre(l.quantite)*en_nombre(l.prix_unitaire_ht)
l=l[l.commande_id.isin(set(oc.commande_id))]
# attention doublons: dedoublonner lignes par commande
cmdlines=lignes.copy(); cmdlines['m']=en_nombre(cmdlines.quantite)*en_nombre(cmdlines.prix_unitaire_ht)
# lignes de la 1ère occurrence seulement
first_idx=commandes.drop_duplicates('commande_id').index
lig_first=pd.json_normalize([brut[i] for i in first_idx],record_path='lignes',meta=['commande_id'])
lig_first['m']=en_nombre(lig_first.quantite)*en_nombre(lig_first.prix_unitaire_ht)
ht_lignes=lig_first.groupby('commande_id').m.sum()
oc=oc.copy(); oc['ht_l']=oc.commande_id.map(ht_lignes); oc['ht_j']=en_nombre(oc.montant_total_ht)
print('ht json vs lignes oct: écarts',((oc.ht_l-oc.ht_j).abs()>0.01).sum())
print('statuts oct',oc.statut.value_counts(dropna=False).to_dict())
norm_st=oc.statut.replace({'LIVRER':'LIVREE','livrée':'LIVREE'})
keep=norm_st.isin(['PAYEE','EXPEDIEE','LIVREE'])
ca_ht_lignes=oc[keep].ht_l.sum(); ca_ht_json=oc[keep].ht_j.sum()
print('CA HT (lignes, statuts payée/expédiée/livrée, dédoublonné)',round(ca_ht_lignes,2),' HT json',round(ca_ht_json,2))
print('avec CREEE: ',round(oc[norm_st.isin(['CREEE','PAYEE','EXPEDIEE','LIVREE'])].ht_l.sum(),2),' toutes statuts', round(oc.ht_l.sum(),2))
oc['ttc']=en_nombre(oc.montant_total_ttc.fillna(oc.total_ttc).astype(str).str.replace(',','.'))
print('TTC oct dédoublonné tous statuts',round(oc.ttc.sum(),2),' TTC retenus',round(oc[keep].ttc.sum(),2), 'ttc>5000', (oc.ttc>5000).sum(), oc[oc.ttc>5000][['commande_id','ttc','ht_l']].to_string())
# valeurs aberrantes: écarts ht json/lignes
ab=oc[(oc.ht_l-oc.ht_j).abs()>0.01]; print(ab[['commande_id','ht_j','ht_l','statut']].to_string())
# Tableau B
p=paiements.copy(); p['t']=en_date(p.event_time); p['m']=en_nombre(p.montant)
po=p[(p.t.dt.tz_convert('Europe/Paris')>='2026-10-01')&(p.t.dt.tz_convert('Europe/Paris')<'2026-11-01')]
acc=po[po.type=='PAYMENT_ACCEPTED']; print('B reproduit: accepted oct',round(acc.m.sum(),2),'/1.2=',round(acc.m.sum()/1.2,2),' publié 438457.68')
acc_utc=p[(p.t>='2026-10-01')&(p.t<'2026-11-01')&(p.type=='PAYMENT_ACCEPTED')]; print('B utc',round(acc_utc.m.sum(),2),round(acc_utc.m.sum()/1.2,2), 'dedoublonné event_id', round(acc_utc.drop_duplicates('event_id').m.sum()/1.2,2))
accd=acc.drop_duplicates('event_id'); ref=po[po.type=='REFUND'].drop_duplicates('event_id')
print('accepted dedup',round(accd.m.sum(),2),'refund',round(ref.m.sum(),2),'neg refunds count',(ref.m<0).sum(),'accepted non-numeric/NaN',acc.m.isna().sum(),'max accepted', acc.m.max(), acc.m.sort_values().tail(5).tolist())
# jointure commandes x paiements
print(controle_jointure(oc[['commande_id','ttc']],po[['commande_id','m','type']],'commande_id'))
jn=oc[['commande_id','ttc']].merge(po[['commande_id','m','type']],on='commande_id'); print('somme ttc après jointure',round(jn.ttc.sum(),2),'avant',round(oc.ttc.sum(),2),'(ligne) cmd brutes (avec doublons) somme ttc brute', round(cmo.ttc.sum(),2))
jn2=cmo[['commande_id','ttc']].merge(po[['commande_id','m']],on='commande_id'); print('jointure naive brute',round(jn2.ttc.sum(),2),' publié 685936.80')
jn3=cmo[['commande_id','montant_total_ht']].assign(h=en_nombre(cmo.montant_total_ht)).merge(po[['commande_id','m']],on='commande_id'); print('jointure ht',round(jn3.h.sum(),2))
print('nb cmd oct',oc.commande_id.nunique(),' lignes jointure',len(jn), ' cmd avec >1 evt paiement',(po.groupby('commande_id').size()>1).sum())
# TTC with payments
print('CA payé net (accepted dédoublonnés - refunds)', round(accd.m.sum()-ref.m.abs().sum(),2), ' /1.2 faux car TVA mixte 5.5/20')
# clients actifs 12 mois
ids=set(clients.client_id)
d12=cu[(cu.d>=pd.Timestamp('2025-11-01',tz='UTC'))&(cu.d<pd.Timestamp('2026-11-01',tz='UTC'))]
print('cmd 12 mois',len(d12))
cid=d12.client_id.fillna(d12.customerId)
print('clients actifs publiés 11429; client_id seul (brut)', d12.client_id.nunique(), ' +customerId', cid.nunique(), ' existants', cid[cid.isin(ids)].nunique())
paid=d12[d12.statut.replace({'LIVRER':'LIVREE','livrée':'LIVREE'}).isin(['PAYEE','EXPEDIEE','LIVREE'])]; cidp=paid.client_id.fillna(paid.customerId)
print('actifs (statut payé+, existants, clé unique)',cidp[cidp.isin(ids)].nunique())
dup_ids=set(clients[clients.client_id.duplicated(keep=False)].client_id); print('clients actifs dont id ambigu (dupliqué CRM)',cidp[cidp.isin(dup_ids)].nunique())
cid_all=cu.client_id.fillna(cu.customerId); print('actif brut toute période',cid_all.nunique(), 'sur 12 mois sans filtre date',cu.client_id.nunique())
# chaîne du froid
c=capteurs.copy(); c['t']=en_nombre(c.temperature); 
print('publié 99.53 : part lignes entre 0 et 4', round(100*c.t.between(0,4).sum()/len(c),2), 'dénominateur',len(c), ' sur non vides',round(100*c.t.between(0,4).sum()/c.t.notna().sum(),2))
c['h']=pd.to_datetime(c.horodatage_local)
ok=c.drop_duplicates(['capteur_id','h'])
ok=ok[(ok.unite=='C')]
ok=ok[ok.t.notna()&(ok.t>-40)&(ok.t<60)]
print('après nettoyage: lignes',len(ok),'conformes 0-4',ok.t.between(0,4).sum(), round(100*ok.t.between(0,4).mean(),2))
f=c.copy(); f.loc[f.unite=='F','t']=(f.t-32)*5/9; f=f.drop_duplicates(['capteur_id','h']); f=f[f.t.between(-40,60)]
print('°F convertis: ',round(100*f.t.between(0,4).mean(),2), len(f))
attendu=3*31*288; print('attendu',attendu,'conformes sur attendu (trou = non conforme)',round(100*f.t.between(0,4).sum()/attendu,2))
fig=valeur_figee(c,'capteur_id','horodatage_local','temperature'); fk=set(zip(fig.capteur_id,fig.horodatage_local))
f2=f[~f.apply(lambda r:(r.capteur_id,r.horodatage_local) in fk,axis=1)]; print('hors figées',round(100*f2.t.between(0,4).mean(),2),len(f2))
print('hors plage 0-4 par capteur',f[~f.t.between(0,4)].groupby('capteur_id').size().to_dict(), f[~f.t.between(0,4)].t.describe().to_dict())
print(f[~f.t.between(0,4)].sort_values('t').head(5)[['capteur_id','horodatage_local','t']].to_string(), f[~f.t.between(0,4)].sort_values('t').tail(5)[['capteur_id','horodatage_local','t']].to_string())
