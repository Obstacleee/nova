from nv import *
j=journaux.copy()
for k in ['lignes_entree','lignes_chargees','lignes_rejetees']: j[k]=pd.to_numeric(j[k],errors='coerce')
print(pd.crosstab(j.traitement,j.statut))
j['ok']=j.lignes_entree==j.lignes_chargees+j.lignes_rejetees
print('bilan KO',(~j.ok).sum()); print(j[~j.ok].to_string())
print(j.regle.value_counts().to_dict())
j['jour']=j.horodatage_utc.str[:10]
echec=j[j.statut!='SUCCES'].sort_values('horodatage_utc'); print(echec.to_string())
print(j.groupby('traitement').horodatage_utc.agg(['min','max','count']))
ic=j[j.traitement=='import_capteurs'].sort_values('jour'); print(ic[['jour','lignes_entree','lignes_chargees','lignes_rejetees','statut']].to_string())
ic2=ic.set_index('jour').lignes_chargees; print(ecart_a_la_reference(ic2).dropna().query("`ecart_%`.abs()>20"))
print('capteurs attendu', 3*288)
ic_all=j[j.traitement=='import_commandes_api'].sort_values('jour'); print(ic_all[['jour','lignes_entree','lignes_chargees','lignes_rejetees','statut','regle']].to_string())
print('taux rejet par traitement', (j.groupby('traitement').lignes_rejetees.sum()/j.groupby('traitement').lignes_entree.sum()*100).round(2).to_dict())
print(lineage.to_string())
