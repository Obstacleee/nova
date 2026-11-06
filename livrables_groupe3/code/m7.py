from nv import *
import unicodedata
print(kpi.to_string())
e=erp.copy(); cl=clients
o=orphelins(e,'client_crm_id',cl,'client_id')
vide=(e.client_crm_id=='').sum(); inc=(~e.client_crm_id.isin(set(cl.client_id))&(e.client_crm_id!='')).sum(); print('vide',vide,'inconnu',inc)
print('erp id prefixes', e.client_erp_id.str[0:2].value_counts().head(5).to_dict(), 'erp_id==crm_id',(e.client_erp_id==e.client_crm_id).sum())
print('crm B-',cl.client_id.str.startswith('B-').sum(), cl[cl.client_id.str.startswith('B-')].canal_creation.value_counts().to_dict(), cl[cl.client_id.str.startswith('B-')].head(3).to_string())
print('crm canal',cl.canal_creation.value_counts().to_dict())
print('prefixes crm',cl.client_id.str.extract(r'^([A-Za-z\-]+)')[0].value_counts().to_dict())
print('erp prefixes',e.client_erp_id.str.extract(r'^([A-Za-z\-]+)')[0].value_counts().to_dict(),'crm_id prefixes',e.client_crm_id.str.extract(r'^([A-Za-z\-]+)')[0].value_counts().to_dict())
cu=cl.drop_duplicates('client_id',keep=False)  # clés uniques seulement
ok=e[e.client_crm_id.isin(set(cl.client_id))].merge(cu,left_on='client_crm_id',right_on='client_id',how='left')
nm=lambda s:s.fillna('').astype(str).str.strip().str.lower()
ok=ok[ok.client_id.notna()]
print('liens valides (clés CRM uniques)',len(ok))
em=ok[(nm(ok.email)!='')&(nm(ok.email_facturation)!='')]
print('email diff',(nm(em.email)!=nm(em.email_facturation)).sum(),'sur',len(em), em[nm(em.email)!=nm(em.email_facturation)][['client_crm_id','email','email_facturation']].head(4).to_string())
print('ville diff',(nm(ok.ville_x)!=nm(ok.ville_y)).sum() if 'ville_x' in ok else '', [c for c in ok.columns if 'ville' in c])
