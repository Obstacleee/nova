from nv import *
cm=commandes.copy()
cm['dl']=en_date(cm.date_commande).dt.tz_convert('Europe/Paris')
o=cm[(cm.dl>='2026-10-01')&(cm.dl<'2026-11-01')].copy()
t=o.montant_total_ttc.fillna(o.total_ttc).astype(str).str.replace(',','.')
o['ttc']=pd.to_numeric(t,errors='coerce'); print('A avec virgules corrigées',round(o.ttc.sum(),2),'cible 568367.00 écart',round(568367-o.ttc.sum(),2))
o2=cm[(cm.date_commande>='2026-10-01')&(cm.date_commande<'2026-11-01')]
t2=pd.to_numeric(o2.montant_total_ttc.fillna(o2.total_ttc).astype(str).str.replace(',','.'),errors='coerce'); print('A texte',round(t2.sum(),2), len(o2))
o3=cm[(cm.dl>='2026-10-01')&(cm.dl<'2026-11-01')&(cm.statut!='ANNULEE')]; print('sans annulées',round(pd.to_numeric(o3.montant_total_ttc.fillna(o3.total_ttc).astype(str).str.replace(',','.'),errors='coerce').sum(),2))
p=paiements.copy(); p['t']=en_date(p.event_time); p['m']=en_nombre(p.montant)
for nm,mask in [('utc',(p.t>='2026-10-01')&(p.t<'2026-11-01')),('paris',(p.t.dt.tz_convert('Europe/Paris')>='2026-10-01')&(p.t.dt.tz_convert('Europe/Paris')<'2026-11-01'))]:
    for ty in [['PAYMENT_ACCEPTED'],['PAYMENT_ACCEPTED','PAYMENT_VALIDATED']]:
        s=p[mask&p.type.isin(ty)]
        print(nm,ty,round(s.m.sum()/1.2,2),'dedup',round(s.drop_duplicates('event_id').m.sum()/1.2,2))
print('cible 438457.68 -> ×1.2 =',round(438457.68*1.2,2))
# recu-based
p['r']=en_date(p.recu); s=p[(p.r>='2026-10-01')&(p.r<'2026-11-01')&(p.type=='PAYMENT_ACCEPTED')]; print('recu',round(s.m.sum()/1.2,2),round(s.drop_duplicates('event_id').m.sum()/1.2,2))
# jointure 685936.80
ci=cm.assign(h=pd.to_numeric(cm.montant_total_ht,errors='coerce'),ttc=pd.to_numeric(cm.montant_total_ttc.fillna(cm.total_ttc).astype(str).str.replace(',','.'),errors='coerce'))
co=ci[(ci.dl>='2026-10-01')&(ci.dl<'2026-11-01')]
pj=p[p.type.notna()]
j=co[['commande_id','ttc','h']].merge(pj[['commande_id','m']],on='commande_id'); print('jointure all events ttc',round(j.ttc.sum(),2),'ht',round(j.h.sum(),2),'cible 685936.80')
j2=co[['commande_id','ttc']].drop_duplicates('commande_id').merge(pj[['commande_id','m']],on='commande_id'); print('dedup cmd',round(j2.ttc.sum(),2))
