from nv import *
cm=commandes.copy()
cu=cm.drop_duplicates('commande_id',keep='first')
print('commandes uniques',len(cu))
f=factures; p=paiements.copy(); g=livraisons; pdfi=pdf
statut=cu.set_index('commande_id').statut
# annulées
ann=set(cu[cu.statut=='ANNULEE'].commande_id)
fac_set=set(f.commande_id); 
pa=p[p.type=='PAYMENT_ACCEPTED']; ref=set(p[p.type=='REFUND'].commande_id)
pay_set=set(pa.commande_id)
liv_set=set(g[g.statut_livraison=='LIVREE'].commande_id)
print('annulées',len(ann),'facturées',len(ann&fac_set),'payées(accepted)',len(ann&pay_set),'payées sans refund',len((ann&pay_set)-ref),'livrées',len(ann&liv_set))
# commandes facturées 2 fois
fc=f.groupby('commande_id').size(); print('facturées 2x',(fc>1).sum(), 'numéros distincts différents', f[f.commande_id.isin(fc[fc>1].index)].groupby('commande_id').numero.nunique().gt(1).sum())
# facture dup numero
d=f[f.duplicated('numero',keep=False)].sort_values('numero'); print(d.head(4).to_string())
# livraison avant commande
gg=g.copy(); gg['d']=en_date(gg.date_livraison); gg['dc']=gg.commande_id.map(en_date(cu.set_index('commande_id').date_commande))
print('livraison avant commande',(gg.d<gg.dc).sum())
# paiement avant commande?
pp=p.copy(); pp['t']=en_date(pp.event_time); pp['dc']=pp.commande_id.map(en_date(cu.set_index('commande_id').date_commande))
print('paiement avant commande (>1h)',(pp.t<pp.dc-pd.Timedelta(hours=1)).sum())
# paiement accepté vs TTC facture
ttc=pd.to_numeric(f.drop_duplicates('commande_id').set_index('commande_id').total_ttc,errors='coerce')
pa2=pa.assign(m=pd.to_numeric(pa.montant,errors='coerce')).drop_duplicates('event_id').groupby('commande_id').m.sum()
j=pd.concat([ttc.rename('ttc'),pa2.rename('pay')],axis=1).dropna()
print('commandes facture+paiement',len(j),'écart>0.01',((j.ttc-j.pay).abs()>0.01).sum())
print((j.pay-j.ttc)[(j.ttc-j.pay).abs()>0.01].describe().to_dict())
# commandes payées sans facture, facturées sans paiement (octobre)
oct_c=cu[en_date(cu.date_commande).dt.strftime('%Y-%m')=='2026-10']
print('commandes octobre',len(oct_c), 'statuts',oct_c.statut.value_counts().to_dict())
print('oct facturées',oct_c.commande_id.isin(fac_set).sum(),'oct payées',oct_c.commande_id.isin(pay_set).sum(), 'oct livrées(gps)',oct_c.commande_id.isin(set(g.commande_id)).sum())
# facturée mais jamais payée
print('factures sans aucun paiement',(~f.commande_id.isin(set(p.commande_id))).sum())
# plusieurs événements de paiement
pe=p.drop_duplicates('event_id'); n=pe.groupby('commande_id').size(); print('commandes avec paiement',len(n),'avec >1 evt',(n>1).sum())
comb=pe.groupby('commande_id').type.apply(lambda s:' + '.join(sorted(s))); print(comb[n>1].value_counts().to_string())
print('commandes dans paiements',pe.commande_id.nunique(),' sans commande JSON',(~pe.commande_id.drop_duplicates().isin(set(cu.commande_id))).sum())
# 10 commandes à suivre
ids=['CMD209']
print(cu[cu.commande_id=='CMD209'].drop(columns=['lignes','_k']).T.to_string())
for t,d in [('factures',f[f.commande_id=='CMD209']),('paiements',p[p.commande_id=='CMD209']),('livraisons',g[g.commande_id=='CMD209']),('pdf',pdf[pdf.commande_id=='CMD209'])]:
    print(t); print(d.to_string())
