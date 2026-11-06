from nv import *
import unicodedata
cl=clients; e=erp
def norm(s): return s.fillna('').map(lambda x:''.join(c for c in unicodedata.normalize('NFD',x.strip().lower()) if unicodedata.category(c)!='Mn'))
print('--- Nadia Benali')

print(e[(e.client_crm_id.isin(['C1042','B-77810']))|(e.client_erp_id.isin(['C1042']))|(norm(e.email_facturation)=='nadia.benali@example.com')].to_string())
print(cl[cl.client_id=='C1042'].T.to_string())
# B- avec email identique à C
b=cl[cl.client_id.str.startswith('B-')]; c_=cl[~cl.client_id.str.startswith('B-')]
m=b.assign(em=norm(b.email)).merge(c_.assign(em=norm(c_.email)),on='em'); m=m[m.em!='']
print('B- email identique à une fiche C',m.client_id_x.nunique(),'/',len(b),' B- sans email', (b.email=='').sum())
# B- même nom prénom + cp
b2=b.assign(k=norm(b.prenom)+'|'+norm(b.nom)); c2=c_.assign(k=norm(c_.prenom)+'|'+norm(c_.nom))
print('B- même nom/prénom qu\'une fiche C',b2.k.isin(set(c2.k)).sum())
# ERP E- ids
print(e[e.client_erp_id.str.startswith('E')].head(3).to_string(), e[e.client_erp_id.str.startswith('E')].client_crm_id.eq('').sum())
# rapprochement: blocage cp + nom normalisé
c3=cl.copy(); c3['k']=norm(c3.prenom)+'|'+norm(c3.nom); c3['em']=norm(c3.email)
same=c3[c3.k.duplicated(keep=False)]
pairs_nom=sum(n*(n-1)//2 for n in same.groupby('k').size())
print('paires même nom+prénom',pairs_nom)
g=c3[c3.em!=''].groupby('em').client_id.nunique(); print('emails partagés par >1 client_id',(g>1).sum())
# règle: même nom+prénom + (même date naissance OU même email OU même tel)
c3['dn']=c3.date_naissance; c3['tel']=c3.telephone.str.replace(r'\D','',regex=True)
cand=c3.merge(c3,on='k'); cand=cand[cand.client_id_x<cand.client_id_y]
sc=(cand.dn_x==cand.dn_y).astype(int)*2+((cand.em_x==cand.em_y)&(cand.em_x!='')).astype(int)*2+((cand.tel_x==cand.tel_y)&(cand.tel_x!='')).astype(int)*1+(cand.code_postal_x==cand.code_postal_y).astype(int)
print('paires candidates',len(cand),'score>=3',(sc>=3).sum(),'score 2',(sc==2).sum(),'score<=1 (homonymes)',(sc<=1).sum())
# --- mission 8
print('--- dérive schéma')
c=commandes.copy(); c['j']=jour(c.date_commande)
t=pd.crosstab(c.j,c.schema_version); print(t.loc['2026-10-10':'2026-10-20'].to_string()); print('1ère 2.0',c[c.schema_version=='2.0'].j.min(), c[c.schema_version=='2.0'].j.max(), c[c.schema_version=='2.0'].date_commande.min())
c['sans']=c.client_id.isna()&c.customerId.isna(); c['sansclient']=c.client_id.isna()
d=c[c.j.between('2026-10-01','2026-10-31')].groupby('j').agg(n=('commande_id','size'),pct_sans_client_id=('sansclient','mean'),v2=('schema_version',lambda s:(s=='2.0').mean()))
d['ecart_vol_%']=ecart_a_la_reference(d.n)['ecart_%']; print(d.round(3).to_string())
print('2.0 champs: telephone null',c[c.schema_version=='2.0']['contact.telephone'].isna().all(),'v1 tel non null', c[c.schema_version=='1.0']['contact.telephone'].notna().sum())
print('v1 colonnes non vides',[k for k in c.columns if c[c.schema_version=='1.0'][k].notna().any() and k not in('lignes',)],'\nv2',[k for k in c.columns if c[c.schema_version=='2.0'][k].notna().any() and k not in('lignes',)])
