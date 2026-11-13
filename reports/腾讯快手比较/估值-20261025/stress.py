"""Sensitivity cases are alternatives, never stacked automatically."""
import copy, json
from decimal import Decimal as D
from model import ROOT, calculate_company, irr, dec, reverse_growth

data=json.loads((ROOT/'model_inputs.json').read_text());fx=dec(data['cny_per_hkd'])
base={n:calculate_company(c,fx) for n,c in data['companies'].items()}
out={}
def run(label,name,change):
    c=copy.deepcopy(data['companies'][name]);change(c)
    r=calculate_company(c,fx)['scenarios']['base']
    out[label]={'company':name,'fair':r['fair_price'],
        'irr3':r['horizons']['3']['irr'],'irr10':r['horizons']['10']['irr']}
def extra_reinvestment(c):
    for a in c['scenarios']['base']['components'][0]['anchors'].values():
        a['net_reinvestment']=str(dec(a['net_reinvestment'])+40)
run('Tencent_annual_reinvestment_plus_40bn','Tencent',extra_reinvestment)
def margin_down(c):
    for a in c['scenarios']['base']['components'][0]['anchors'].values():
        a['margin']=str(dec(a['margin'])-D('.02'))
run('Kuaishou_platform_margin_minus_2pp','Kuaishou',margin_down)
def fully_fund(c): c['scenarios']['base']['components'][1]['loss_funding_share']='1'
run('Kuaishou_parent_funds_all_Kling_losses','Kuaishou',fully_fund)
def lower_share(c): c['scenarios']['base']['components'][1]['ownership']='.50'
run('Kuaishou_only_positive_Kling_cash_share_50pct','Kuaishou',lower_share)
def paid(c):c['scenarios']['base']['bridge']=str(dec(c['scenarios']['base']['bridge'])+D('20.4471')*D('.6833'))
run('Kuaishou_all_financing_paid_unused_no_claim_adjustment_upper_bound','Kuaishou',paid)
def no_kling(c):c['scenarios']['base']['components']=c['scenarios']['base']['components'][:1]
run('Kuaishou_Kling_removed_no_more_cost_no_salvage','Kuaishou',no_kling)
def full_payout(c): c['dividend_payout']='1'
run('Tencent_full_cash_distribution_alternative','Tencent',full_payout)
run('Kuaishou_full_cash_distribution_alternative','Kuaishou',full_payout)
for name, starts in [('Tencent',['120','150','180']),('Kuaishou',['5','8','12'])]:
    out[name+'_reverse_starting_cash_sensitivity']={}
    for v in starts:
        c=copy.deepcopy(data['companies'][name]);c['normalized_starting_fcff']=v
        out[name+'_reverse_starting_cash_sensitivity'][v]=reverse_growth(c,fx)['growth']
    out[name+'_expected_cashflow_entry_prices']={}
    for h in ('3','10'):
        f=base[name]['weighted'][h]['cashflows']
        out[name+'_expected_cashflow_entry_prices'][h]={str(target):sum((x/(1+target)**t for t,x in enumerate(f) if t),D(0))
                for target in (D('.12'),D('.15'))}

# NPV at Tencent expected-cashflow IRR is linear in Kuaishou scenario probabilities.
# Keep bull 15%, transfer probability between bear and base. This is subjective sensitivity.
threshold={}
for h in ('3','10'):
    r=base['Tencent']['weighted'][h]['irr_of_expected_cashflows']
    v={}
    for name,s in base['Kuaishou']['scenarios'].items():
        f=s['horizons'][h]['cashflows']
        v[name]=sum((x/(1+r)**i for i,x in enumerate(f)),D(0))
    threshold[h]=-(D('.85')*v['base']+D('.15')*v['bull'])/(v['bear']-v['base'])
out['Kuaishou_bear_probability_break_even_vs_Tencent']=threshold
out['fx_multiply_terminal_HKD']={'CNY_annual_depreciation_2pct_3y':D('.98')**3,
    'CNY_annual_depreciation_2pct_10y':D('.98')**10}
(ROOT/'stress_results.json').write_text(json.dumps(out,ensure_ascii=False,indent=2,default=str)+'\n')
for k,v in out.items():print(k, v)
