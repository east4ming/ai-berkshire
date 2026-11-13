"""Optional check against this checkout's shared valuation engine.
The standalone model.py remains sufficient to reproduce the published model.
"""
from pathlib import Path
import json, subprocess, sys
from decimal import Decimal as D
from model import ROOT, schedule, component_value
repo=ROOT.parents[2]
d=json.loads((ROOT/'model_inputs.json').read_text());fx=D(d['cny_per_hkd'])
records=[]
for company,c in d['companies'].items():
 for scenario,s in c['scenarios'].items():
  comp=s['components'][0];rows=schedule(comp)
  # This reference validates only the core FCFF component. Kling has separate
  # equity capital calls and a zero-terminal failure path outside engine support.
  m={
   'schema_version':1,'name':company+' '+scenario+' core component reference',
   'synthetic':False,'valuation_date':'2026-10-23','data_cutoff':'2026-10-23',
   'timing':'annual_end_of_year','cash_flow_type':'FCFF','risk_adjustment':'risk_adjusted',
   'cash_flow_basis':'nominal','cash_flow_currency':'CNY','quote_currency':'HKD',
   'value_scale':'1000000000','quote_currency_per_cashflow_currency':str(1/fx),
   'ordinary_shares':c['model_shares'],'shares_scale':'1000000000',
   'shares_as_of':'2026-10-23','ordinary_shares_per_quote_unit':'1',
   'equity_bridge':{'excess_cash':{'amount':'0','excluded_from_cash_flows':True,'rationale':'Component-only mathematical check; full bridge in model_inputs.json'},
    'nonoperating_investments':{'amount':'0','excluded_from_cash_flows':True,'rationale':'No investment income inside core FCFF'},
    'debt':'0','noncontrolling_interests':'0','other_equity_claims':'0'},
   'accounting_notes':{
    'sbc':'Future new-grant economic cost retained in margin; existing rights represented by approximate economic share denominator. This is not a legal cap-table audit.',
    'buybacks':'Static shares; no extra repurchase return. Holding model records dividends and retained cash separately.',
    'leases':'Cash rent included in operating margins/reinvestment; same lease debt not deducted again.',
    'cash_flow_adjustments':'Cash-taxed operating profit less net reinvestment; operating minority proxy already applied for Tencent. Nonoperating income excluded.',
    'discount_rate':'Research assumption: CNY nominal risk-adjusted WACC; official 10Y reference1.64%, premiums and capital weights are assumptions.',
    'terminal':'Next-year cash retains net reinvestment; growth times year10 cash, no second growth multiplication.'},
   'scenarios':[{'name':scenario,'probability':'1','discount_rate':{'value':comp['rate'],'kind':'wacc','currency':'CNY','basis':'nominal'},
    'cash_flows':[{'year':r['year'],'amount':str(r['attributable_fcff'])} for r in rows],
    'terminal':{'method':'next_year_cash_flow','growth_rate':comp['g'],'currency':'CNY','basis':'nominal',
     'next_year_cash_flow':str(rows[-1]['attributable_fcff']*(1+D(comp['g'])))}}]}
  tmp=ROOT/'audit'/'engine_input.tmp.json';res=ROOT/'audit'/'engine_output.tmp.json'
  tmp.write_text(json.dumps(m,indent=2)+'\n')
  p=subprocess.run([sys.executable,str(repo/'tools/company_valuation.py'),'--input',str(tmp),'--output',str(res)],capture_output=True,text=True)
  if p.returncode:raise RuntimeError(p.stderr+p.stdout)
  output=json.loads(res.read_text())
  reference_value=D(output['scenarios'][0]['operating_present_value'])
  standalone_value=component_value(comp,rows)['value']
  assert abs(reference_value-standalone_value)<D('1e-30')
  # Preserve complete response so its contract remains auditable.
  records.append({'company':company,'scenario':scenario,'input':m,'output':output,
                  'standalone_component_value':str(standalone_value),'absolute_difference':str(abs(reference_value-standalone_value)),'status':'PASS'})
tmp.unlink();res.unlink()
(ROOT/'audit/engine_reference.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
print('Shared valuation engine completed six core-component references; compare with independent_verification.json.')
