from nv import *
# doublons clients: contenu
d=clients[clients.duplicated('client_id',keep=False)]
nun=d.groupby('client_id').apply(lambda x:len(x.drop_duplicates()),include_groups=False)
print('clients dup: clés',len(nun),'contenu identique',(nun==1).sum(),'différent',(nun>1).sum())
# R01 décomposition
ids=set(clients.client_id)
c=commandes.copy()
c['cid']=c['client_id'].fillna(c['customerId'])
sans=c['client_id'].isna()&c['customerId'].isna()
autre=c['client_id'].isna()&c['customerId'].notna()
print('R01 total',(~c.client_id.isin(ids)).sum(),'| sans aucun id',sans.sum(),'| customerId',autre.sum(),'| customerId inconnu',(autre&~c.cid.isin(ids)).sum(),'| client_id présent inconnu',(c.client_id.notna()&~c.client_id.isin(ids)).sum())
print('R01 après correction nom champ: inconnus', (c.cid.notna()&~c.cid.isin(ids)).sum(), ' par version', c[c.cid.notna()&~c.cid.isin(ids)].schema_version.value_counts().to_dict())
print(c[c.cid.notna()&~c.cid.isin(ids)].cid.head(8).tolist())
# clients vides?
print('client_id vide str',(c.client_id=='').sum())
# produits
print("orph produits"); o=orphelins(lignes,'produit_id',produits,'produit_id'); print(o.produit_id.value_counts().head(5).to_dict(), o.produit_id.nunique())
print('produits dup'); doublons(produits,'produit_id').head(4)
# factures->commandes
o=orphelins(factures,'commande_id',commandes,'commande_id'); print(o.head(3).to_string())
dupf=doublons(factures,'numero'); dupc=doublons(factures,'commande_id'); print(len(dupc))
# montants
l=lignes.copy(); l['q']=en_nombre(l['quantite']); l['p']=en_nombre(l['prix_unitaire_ht']); l['m']=l.q*l.p
print('lignes q<=0',(l.q<=0).sum(),'p<=0',(l.p<=0).sum(),'p>1000',(l.p>1000).sum(),'q>50',(l.q>50).sum(), l.p.describe().to_dict())
s=l.groupby('commande_id')['m'].sum()
cc=commandes.drop_duplicates('commande_id').copy()
cc['ht']=en_nombre(cc['montant_total_ht']); cc['calc']=cc.commande_id.map(s)
ec=cc[(cc.ht-cc.calc).abs()>0.01]
print('montant HT: contrôlées',len(cc),'écarts',len(ec),'NaN',cc.ht.isna().sum()); print(ec[['commande_id','montant_total_ht','calc','statut']].head(8).to_string())
print(ec.assign(r=ec.ht/ec.calc).r.describe())
print('HT>5000',(cc.ht>5000).sum(), cc.ht.describe().to_dict())
cc['ttc']=en_nombre(cc['montant_total_ttc'].fillna(cc['total_ttc']))
print('TTC/HT ratio',(cc.ttc/cc.ht).describe().to_dict())
print('ttc manquant',cc.ttc.isna().sum())
# factures
f=factures.copy()
for k in ['total_ht','total_tva','total_ttc']: f[k]=en_nombre(f[k])
r03=f[(f.total_ttc-f.total_ht-f.total_tva).abs()>0.01]; print('R03',len(r03)); print(r03.head(5).to_string())
print('factures ttc <=0',(f.total_ttc<=0).sum(), f.total_ttc.describe().to_dict(), f.devise.value_counts().to_dict())
# factures vs commande totaux
m=f.merge(cc[['commande_id','ht','calc','statut','date_commande','ttc']],on='commande_id',how='left')
print('facture ht != cmd ht',((m.total_ht-m.ht).abs()>0.01).sum(),'sur',m.ht.notna().sum())
# dates
cl=clients.copy()
cl['dc']=en_date(cl.date_creation); cl['dm']=en_date(cl.date_maj); cl['dn']=en_date(cl.date_naissance)
print('maj<creation',(cl.dm<cl.dc).sum(),'naiss future',(cl.dn>pd.Timestamp('2026-11-01',tz='UTC')).sum(),'naiss<1900',(cl.dn<pd.Timestamp('1900-01-01',tz='UTC')).sum(),'age<16',(cl.dn>pd.Timestamp('2010-11-01',tz='UTC')).sum(), cl.dn.min(),cl.dn.max())
print('creation future',(cl.dc>pd.Timestamp('2026-11-01',tz='UTC')).sum(), 'maj future',(cl.dm>pd.Timestamp('2026-11-01',tz='UTC')).sum())
cm=commandes.copy(); cm['d']=en_date(cm.date_commande)
print('cmd future',(cm.d>pd.Timestamp('2026-11-01',tz='UTC')).sum(), cm.d.min(), cm.d.max())
print('cmd dates non ISO / sans tz:', cm.date_commande.str.contains(r'(Z|[+-]\d{2}:\d{2})$').eq(False).sum())
m['de']=en_date(m.date_emission); m['dcmd']=en_date(m.date_commande)
print('facture avant commande',(m.de.dt.normalize()<m.dcmd.dt.normalize()).sum(),'sur',m.dcmd.notna().sum())
print(m[(m.de.dt.normalize()<m.dcmd.dt.normalize())][['numero','commande_id','date_emission','date_commande']].head(5).to_string())
print('factures hors sept-oct', m.de.dt.strftime('%Y-%m').value_counts().to_dict())
print('statuts commande normalisés', commandes.statut.value_counts(dropna=False).to_dict())
print('canal', commandes.canal.value_counts().to_dict())
