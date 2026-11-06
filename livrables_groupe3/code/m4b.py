from nv import *
f=factures
print('numero vide',(f.numero.isna()|(f.numero=='')).sum(), f.numero.isna().sum())
fn=f[f.numero.notna()]; print('numero dup (non vides)',fn.numero.duplicated(keep=False).sum(), fn[fn.numero.duplicated(keep=False)].numero.nunique())
print(fn[fn.numero.duplicated(keep=False)].sort_values('numero').head(4).to_string())
print('cmd209 dans json?', (commandes.commande_id=='CMD209').sum(), commandes[commandes.commande_id.str.match(r'^CMD20\d$')].commande_id.tolist()[:5])
for t,d in [('factures',f[f.commande_id=='CMD209']),('paiements',paiements[paiements.commande_id=='CMD209']),('livraisons',livraisons[livraisons.commande_id=='CMD209']),('pdf',pdf[pdf.commande_id=='CMD209'])]:
    print(t); print(d.to_string())
print(commandes[commandes.commande_id=='CMD209'].drop(columns='lignes').T.to_string())
# écarts paiement vs ttc distribution
cu=commandes.drop_duplicates('commande_id')
ttc=pd.to_numeric(f.dropna(subset=['numero']).drop_duplicates('commande_id').set_index('commande_id').total_ttc,errors='coerce')
pa=paiements[paiements.type=='PAYMENT_ACCEPTED'].drop_duplicates('event_id'); pa=pa.assign(m=pd.to_numeric(pa.montant,errors='coerce'))
n=pa.groupby('commande_id').size(); one=pa[pa.commande_id.isin(n[n==1].index)].set_index('commande_id').m
j=pd.concat([ttc.rename('ttc'),one.rename('pay')],axis=1).dropna(); d=(j.pay-j.ttc).round(2)
print('1 seul accepté: n',len(j),'écart>0.05',(d.abs()>0.05).sum(),'écart 0.01-0.05',((d.abs()>0.01)&(d.abs()<=0.05)).sum())
print(d[d.abs()>0.05].describe().to_dict()); print(j[d.abs()>0.05].head(6).to_string())
print('ratio', (j.pay/j.ttc)[d.abs()>0.05].round(2).value_counts().head(5).to_dict())
